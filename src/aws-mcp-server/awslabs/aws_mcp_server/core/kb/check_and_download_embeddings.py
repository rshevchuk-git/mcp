# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from .dense_retriever import KNOWLEDGE_BASE_SUFFIX
from awscli.clidriver import __version__ as awscli_version
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f'Running: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if result.stdout:
        print(f'STDOUT: {result.stdout[:500]}...')  # Truncate long output
    if result.stderr:
        print(f'STDERR: {result.stderr}')
    return result


def get_latest_artifact() -> Optional[dict]:
    """Get the latest dist-aws-mcp-server artifact from GitHub."""
    try:
        # Get repository owner from GITHUB_REPOSITORY environment variable
        repo = os.environ.get('GITHUB_REPOSITORY', 'awslabs/mcp')
        owner = repo.split('/')[0]

        # Get artifacts (first page only)
        cmd = [
            'gh',
            'api',
            '-H',
            'Accept: application/vnd.github+json',
            '-H',
            'X-GitHub-Api-Version: 2022-11-28',
            f'/repos/{owner}/mcp/actions/artifacts?name=dist-aws-mcp-server&per_page=10',
        ]

        result = run_command(cmd)

        # Parse the response - GitHub API returns a single JSON object
        try:
            artifacts_data = json.loads(result.stdout)
            if 'artifacts' in artifacts_data:
                all_artifacts = artifacts_data['artifacts']
                print(f'Found {len(all_artifacts)} artifacts in response')
            else:
                print('No artifacts found in response')
                all_artifacts = []
        except json.JSONDecodeError as e:
            print(f'Error parsing JSON response: {e}')
            print(f'Response preview: {result.stdout[:500]}...')
            all_artifacts = []

        # Sort by creation date and get the latest
        if all_artifacts:
            latest_artifact = max(all_artifacts, key=lambda x: x['created_at'])
            print(
                f'Found latest artifact: {latest_artifact["name"]} created at {latest_artifact["created_at"]}'
            )
            return latest_artifact

        print('No artifacts found')
        return None

    except subprocess.CalledProcessError as e:
        print(f'Error getting artifacts: {e}')
        return None
    except Exception as e:
        print(f'Unexpected error: {e}')
        return None


def is_within_directory(directory: Path, target: Path) -> bool:
    """Check if the target path is within the given directory."""
    try:
        directory = directory.resolve()
        target = target.resolve()
        return str(target).startswith(str(directory))
    except Exception:
        return False


def safe_extract_zip(zip_ref: zipfile.ZipFile, path: Path):
    """Safely extract zip file to the given path, preventing path traversal."""
    for member in zip_ref.namelist():
        member_path = path / member
        if not is_within_directory(path, member_path):
            raise Exception(f'Unsafe zip file member: {member}')
        # Create parent directories if needed
        member_path.parent.mkdir(parents=True, exist_ok=True)
        if not member.endswith('/'):  # skip directories
            with zip_ref.open(member) as source, open(member_path, 'wb') as target:
                target.write(source.read())


def safe_extract_tar(tar_ref: tarfile.TarFile, path: Path):
    """Safely extract tar file to the given path, preventing path traversal."""
    for member in tar_ref.getmembers():
        member_path = path / member.name
        if not is_within_directory(path, member_path):
            raise Exception(f'Unsafe tar file member: {member.name}')
        tar_ref.extract(member, path)


def download_artifact(artifact: dict) -> tuple[bool, Optional[Path]]:
    """Download the artifact and extract it. Returns (success, extracted_dir_path)."""
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix='embeddings_download_'))
        print(f'Created temporary directory: {temp_dir}')

        # Download the artifact
        cmd = [
            'gh',
            'api',
            '-H',
            'Accept: application/vnd.github+json',
            '-H',
            'X-GitHub-Api-Version: 2022-11-28',
            artifact['archive_download_url'],
        ]

        # Download as binary
        result = subprocess.run(cmd, capture_output=True, check=True)

        # Save to file in temp directory
        artifact_zip = temp_dir / 'artifact.zip'
        with open(artifact_zip, 'wb') as f:
            f.write(result.stdout)

        print('Downloaded artifact.zip')

        # Extract the zip file
        with zipfile.ZipFile(artifact_zip, 'r') as zip_ref:
            safe_extract_zip(zip_ref, temp_dir)

        print('Extracted artifact.zip')

        # Find the tar.gz file and extract it
        tar_files = list(temp_dir.glob('*.tar.gz'))
        if not tar_files:
            print('No tar.gz file found in artifact')
            return False, None

        tar_file = tar_files[0]
        print(f'Found tar file: {tar_file}')

        # Extract the tar.gz file
        with tarfile.open(tar_file, 'r:gz') as tar_ref:
            safe_extract_tar(tar_ref, temp_dir)

        print(f'Extracted {tar_file}')

        # Find the extracted directory
        extracted_dirs = [
            d for d in temp_dir.iterdir() if d.is_dir() and d.name.startswith('awslabs')
        ]
        if not extracted_dirs:
            print('No extracted directory found')
            return False, None

        extracted_dir = extracted_dirs[0]
        print(f'Found extracted directory: {extracted_dir}')

        return True, extracted_dir

    except Exception as e:
        print(f'Error downloading/extracting artifact: {e}')
        return False, None


def check_embeddings_file(extracted_dir: Path) -> Optional[Path]:
    """Check if embeddings file exists with the correct awscli version."""
    embeddings_dir = extracted_dir / 'awslabs' / 'aws_mcp_server' / 'core' / 'data' / 'embeddings'

    if not embeddings_dir.exists():
        print(f'Embeddings directory not found: {embeddings_dir}')
        return None

    # Look for embeddings file with the correct awscli version
    expected_pattern = f'{KNOWLEDGE_BASE_SUFFIX}-{awscli_version}.npz'
    matching_files = list(embeddings_dir.glob(expected_pattern))

    if matching_files:
        embeddings_file = matching_files[0]
        print(f'Found matching embeddings file: {embeddings_file}')
        return embeddings_file

    print(f'No embeddings file found matching pattern: {expected_pattern}')
    return None


def copy_embeddings_file(embeddings_file: Path, target_dir: Path) -> bool:
    """Copy the embeddings file to the target directory."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / embeddings_file.name

        # Copy the file
        import shutil

        shutil.copy2(embeddings_file, target_file)
        print(f'Copied embeddings file to: {target_file}')
        return True

    except Exception as e:
        print(f'Error copying embeddings file: {e}')
        return False


def cleanup(temp_dir: Optional[Path] = None):
    """Clean up temporary directory."""
    if temp_dir and temp_dir.exists():
        try:
            import shutil

            shutil.rmtree(temp_dir)
            print(f'Removed temporary directory: {temp_dir}')
        except Exception as e:
            print(f'Error removing temporary directory: {e}')


def check_local_embeddings() -> bool:
    """Check if embeddings file already exists locally."""
    embeddings_dir = Path('awslabs/aws_mcp_server/core/data/embeddings')
    if not embeddings_dir.exists():
        return False

    # Look for embeddings file with the correct awscli version
    expected_pattern = f'{KNOWLEDGE_BASE_SUFFIX}-{awscli_version}.npz'
    matching_files = list(embeddings_dir.glob(expected_pattern))

    if matching_files:
        print(f'Found local embeddings file: {matching_files[0]}')
        return True

    return False


def check_gh_cli() -> bool:
    """Check if GitHub CLI is available."""
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True, check=True)
        print(f'GitHub CLI version: {result.stdout.split()[2]}')
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print('GitHub CLI not available')
        return False


def main():
    """Main function."""
    print('Checking for existing embeddings...')

    print(f'Current awscli version: {awscli_version}')

    # Check if embeddings already exist locally
    if check_local_embeddings():
        print('Embeddings already exist locally')
        return True

    # Check if GitHub CLI is available
    if not check_gh_cli():
        print('GitHub CLI not available, will generate embeddings')
        return False

    # Get latest artifact
    artifact = get_latest_artifact()
    if not artifact:
        print('No artifact found, will generate embeddings')
        return False

    # Download and extract artifact
    success, extracted_dir = download_artifact(artifact)
    if not success or not extracted_dir:
        print('Failed to download artifact, will generate embeddings')
        return False

    # Check for embeddings file
    embeddings_file = check_embeddings_file(extracted_dir)
    if not embeddings_file:
        print('No matching embeddings file found, will generate embeddings')
        cleanup(extracted_dir.parent)  # Clean up the temp directory
        return False

    # Copy embeddings file to current directory
    target_dir = Path('awslabs/aws_mcp_server/core/data/embeddings')
    if copy_embeddings_file(embeddings_file, target_dir):
        print('Successfully copied embeddings file')
        cleanup(extracted_dir.parent)  # Clean up the temp directory
        return True
    else:
        print('Failed to copy embeddings file, will generate embeddings')
        cleanup(extracted_dir.parent)  # Clean up the temp directory
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
