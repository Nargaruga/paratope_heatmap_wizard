import os
import sys
from pathlib import Path
import subprocess


def main():
    wizard_root = sys.argv[1]
    env_name = sys.argv[2]

    if os.name == "nt":
        prefix = ["powershell.exe"]
    else:
        prefix = []

    if os.name != "nt":
        # install muscle manually
        print("Installing MUSCLE...")
        muscle_dir = os.path.join(wizard_root, "ext", "muscle")
        Path(muscle_dir).mkdir(exist_ok=True)
        subprocess.run(
            [
                "conda",
                "run",
                "--no-capture-output",
                "-n",
                f"{env_name}",
                "wget",
                "https://www.drive5.com/muscle/muscle_src_3.8.1551.tar.gz",
            ],
            cwd=muscle_dir,
        )

        subprocess.run(
            [
                "conda",
                "run",
                "--no-capture-output",
                "-n",
                f"{env_name}",
                "tar",
                "xzvf",
                "muscle_src_3.8.1551.tar.gz",
            ],
            cwd=muscle_dir,
        )

        subprocess.run(
            [
                "conda",
                "run",
                "--no-capture-output",
                "-n",
                f"{env_name}",
                "make",
            ],
            cwd=muscle_dir,
        )

        conda_base_path = str(
            subprocess.check_output("conda info --base", shell=True), "utf-8"
        ).strip()
        conda_prefix = os.path.join(conda_base_path, "envs", env_name)
        subprocess.run(
            [
                "conda",
                "run",
                "--no-capture-output",
                "-n",
                f"{env_name}",
                "cp",
                "muscle",
                os.path.join(conda_prefix, "bin"),
            ],
            cwd=muscle_dir,
        )

        try:
            subprocess.run(
                [
                    "conda",
                    "run",
                    "--no-capture-output",
                    "-n",
                    f"{env_name}",
                    "ANARCI",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print("Installing ANARCI...")
            anarci_dir = os.path.join(wizard_root, "ext", "ANARCI")
            subprocess.run(
                [
                    "conda",
                    "run",
                    "--no-capture-output",
                    "-n",
                    f"{env_name}",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(anarci_dir, "requirements.txt"),
                ],
                cwd=anarci_dir,
                check=True,
            )

            subprocess.run(
                [
                    "conda",
                    "run",
                    "--no-capture-output",
                    "-n",
                    f"{env_name}",
                    "python",
                    "setup.py",
                    "install",
                ],
                cwd=anarci_dir,
                check=True,
            )

    print("Installing Parapred...")
    parapred_dir = os.path.join(wizard_root, "ext", "parapred-pytorch")
    subprocess.run(
        prefix
        + [
            "conda",
            "run",
            "--no-capture-output",
            "-n",
            env_name,
            "pip",
            "install",
            "-r",
            os.path.join(parapred_dir, "requirements.txt"),
        ],
        cwd=parapred_dir,
        check=True,
    )

    if os.name == "nt":
        subprocess.run(
            [
                "powershell.exe",
                "Invoke-WebRequest",
                "-Uri",
                "https://github.com/alchemab/parapred-pytorch/raw/refs/tags/v1.0.2/parapred/weights/parapred_pytorch.h5",
                "-OutFile",
                os.path.join(wizard_root, "weights", "parapred_pytorch.h5"),
            ],
            check=True,
        )
    else:
        subprocess.run(
            [
                "wget",
                "-nc",
                "https://github.com/alchemab/parapred-pytorch/raw/refs/tags/v1.0.2/parapred/weights/parapred_pytorch.h5",
                "-P",
                "weights",
            ],
            cwd=wizard_root,
            check=True,
        )

    if os.name == "nt":
        subprocess.run(
            'C:\\cygwin64\\bin\\bash -c "export PATH=/bin:/usr/bin:$PATH && make install"',
            cwd=parapred_dir,
            shell=True,
            check=True,
        )
    else:
        subprocess.run(
            ["make", "install"],
            cwd=parapred_dir,
            check=True,
        )


if __name__ == "__main__":
    main()
