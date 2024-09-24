import subprocess
from pathlib import Path
from typing import List

from aws_cdk.aws_lambda import Architecture
from dirhash import dirhash

from aws_lambda_powertools import PACKAGE_PATH
from tests.e2e.utils.constants import CDK_OUT_PATH, SOURCE_CODE_ROOT_PATH
from tests.e2e.utils.lambda_layer.base import BaseLocalLambdaLayer


class LocalLambdaPowertoolsLayer(BaseLocalLambdaLayer):
    IGNORE_EXTENSIONS = ["pyc"]
    ARCHITECTURE_PLATFORM_MAPPING = {
        Architecture.X86_64.name: ("manylinux_2_17_x86_64", "manylinux_2_28_x86_64"),
        Architecture.ARM_64.name: ("manylinux_2_17_aarch64", "manylinux_2_28_aarch64"),
    }

    def __init__(self, output_dir: Path = CDK_OUT_PATH, architecture: Architecture = Architecture.X86_64):
        super().__init__(output_dir)
        self.package = f"{SOURCE_CODE_ROOT_PATH}[all,redis,datamasking]"

        self.platform_args = self._resolve_platform(architecture)
        self.build_args = f"{self.platform_args} --only-binary=:all: --upgrade"
        self.build_command = f"python -m pip install {self.package} {self.build_args} --target {self.target_dir}"
        self.cleanup_command = (
            f"rm -rf {self.target_dir}/boto* {self.target_dir}/s3transfer* && "
            f"rm -rf {self.target_dir}/*dateutil* {self.target_dir}/urllib3* {self.target_dir}/six* && "
            f"rm -rf {self.target_dir}/jmespath* && "
            f"find {self.target_dir} -name '*.so' -type f -exec strip '{{}}' \\; && "
            f"find {self.target_dir} -wholename '*/tests/*' -type f -delete && "
            f"find {self.target_dir} -regex '^.*\\(__pycache__\\|\\.py[co]\\)$' -delete"
        )
        self.source_diff_file: Path = CDK_OUT_PATH / "layer_build.diff"

    def build(self) -> str:
        self.before_build()

        if self._has_source_changed():
            subprocess.run(self.build_command, shell=True, check=True)

        self.after_build()

        return str(self.output_dir)

    def after_build(self):
        subprocess.run(self.cleanup_command, shell=True, check=True)

    def _has_source_changed(self) -> bool:
        """Hashes source code and

        Returns
        -------
        change : bool
            Whether source code hash has changed
        """
        diff = self.source_diff_file.read_text() if self.source_diff_file.exists() else ""
        new_diff = dirhash(directory=PACKAGE_PATH, algorithm="md5", ignore=self.IGNORE_EXTENSIONS)
        if new_diff != diff or not self.output_dir.exists():
            self.source_diff_file.write_text(new_diff)
            return True

        return False

    def _resolve_platform(self, architecture: Architecture) -> str:
        """Returns the correct pip platform tag argument for the manylinux project (see PEP 599)

        Returns
        -------
        str
            pip's platform argument, e.g., --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64
        """
        platforms = self.ARCHITECTURE_PLATFORM_MAPPING.get(architecture.name)
        if not platforms:
            raise ValueError(
                f"unknown architecture {architecture.name}. Supported: {self.ARCHITECTURE_PLATFORM_MAPPING.keys()}",
            )

        return self._build_platform_args(platforms)

    def _build_platform_args(self, platforms: List[str]):
        return " ".join([f"--platform {platform}" for platform in platforms])
