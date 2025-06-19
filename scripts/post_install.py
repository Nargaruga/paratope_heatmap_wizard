import os
import sys
from pathlib import Path
import shutil
import subprocess


class ANARCINotFoundError(Exception):
    pass


def check_anarci_installation(env_name):
    if os.name == "nt":
        import docker

        client = docker.from_env()
        image_name = "anarci:latest"
        filterred_images = client.images.list(filters={"reference": image_name})

        if len(filterred_images) == 0:
            raise ANARCINotFoundError("ANARCI image not found.")
    else:
        try:
            subprocess.run(
                [
                    "conda",
                    "run",
                    "--no-capture-output",
                    "-n",
                    f"{env_name}",
                    "which",
                    "ANARCI",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            raise ANARCINotFoundError("ANARCI not found in conda environment.")


def install_muscle(wizard_root, env_name):
    print("Installing MUSCLE...")
    muscle_dir = os.path.join(wizard_root, "ext", "muscle")
    shutil.rmtree(Path(muscle_dir), ignore_errors=True)
    Path(muscle_dir).mkdir()
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
        check=True,
    )

    subprocess.run(
        [
            "tar",
            "xzvf",
            "muscle_src_3.8.1551.tar.gz",
        ],
        cwd=muscle_dir,
        check=True,
    )

    os.remove(os.path.join(muscle_dir, "muscle_src_3.8.1551.tar.gz"))

    subprocess.run(
        f"conda run --no-capture-output -n {env_name} make",
        cwd=muscle_dir,
        shell=True,
        check=True,
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
        check=True,
    )


def install_anarci(wizard_root, env_name):
    if os.name == "nt":
        print("Building ANARCI image...")
        subprocess.run(
            [
                "docker",
                "build",
                "-f",
                os.path.join(wizard_root, "docker", "anarci.Dockerfile"),
                "--tag",
                "anarci:latest",
                os.path.join(wizard_root, "ext", "ANARCI"),
            ],
            check=True,
        )
    else:
        install_muscle(wizard_root, env_name)

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


def main():
    wizard_root = sys.argv[1]
    env_name = sys.argv[2]

    if os.name == "nt":
        prefix = ["powershell.exe"]
    else:
        prefix = []

    try:
        check_anarci_installation(env_name)
    except ANARCINotFoundError:
        install_anarci(wizard_root, env_name)

    parapred_dir = os.path.join(wizard_root, "ext", "parapred-pytorch")
    try:
        if os.name == "nt":
            prefix = ["powershell.exe"]
        else:
            prefix = []

        subprocess.run(
            "conda list --name parapred",
            check=True,
            shell=True,
        )
    except subprocess.CalledProcessError:
        print("Installing Parapred...")

        subprocess.run(
            prefix
            + [
                "conda",
                "env",
                "create",
                "--name",
                "parapred",
                "--file",
                os.path.join(parapred_dir, "environment.yml"),
            ],
            check=True,
        )

        if os.name == "nt":
            subprocess.run(
                [
                    "powershell.exe",
                    "conda",
                    "run",
                    "--no-capture-output",
                    "--name",
                    "parapred",
                    "pip",
                    "install",
                    ".",
                ],
                cwd=parapred_dir,
                check=True,
            )
        else:
            subprocess.run(
                [
                    "conda",
                    "run",
                    "--no-capture-output",
                    "--name",
                    "parapred",
                    "make",
                    "install",
                ],
                cwd=parapred_dir,
                check=True,
            )


if __name__ == "__main__":
    main()
