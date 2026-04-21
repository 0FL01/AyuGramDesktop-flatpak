# Building the AyuGram Flatpak

This guide describes the complete process for creating a Flatpak package for AyuGram. The process consists of two main stages:

1.  **Building the AyuGram binary** using the official Docker environment.
2.  **Packaging the built binary** and necessary resources into a Flatpak package.

## Prerequisites

This guide was tested on **Fedora 42** (inside a Toolbx container) but should work on most modern Linux distributions.

Before you begin, ensure that the following components are installed on your system:

*   `git`
*   `docker`
*   `flatpak`
*   `flatpak-builder`

Also, make sure your user is added to the `docker` group to run commands without `sudo`.

```bash
# Example for Fedora/Ubuntu
sudo usermod -aG docker $USER
# You will need to log out and log back in for this change to take effect
```

## Step 1: Build the AyuGram Binary

First, you need to build the application itself by following the official instructions.

1.  **Clone the AyuGram repository:**
    Choose a directory for the build and run the command. Note that this will create a directory named `tdesktop`.

    ```bash
    git clone --recursive https://github.com/AyuGram/AyuGramDesktop.git tdesktop
    cd tdesktop
    ```

2.  **Prepare the libraries:**
    Run the preparation script. You might need `poetry` for this.

    ```bash
    # If poetry is not installed: pip install poetry
    ./Telegram/build/prepare/linux.sh
    ```

3.  **Build the project using Docker:**
    This command will run the build in an isolated CentOS environment.

    ```bash
    docker run --rm -it \
        -u $(id -u) \
        -v "$PWD:/usr/src/tdesktop" \
        ghcr.io/telegramdesktop/tdesktop/centos_env:latest \
        /usr/src/tdesktop/Telegram/build/docker/centos_env/build.sh \
        -D TDESKTOP_API_ID=2040 \
        -D TDESKTOP_API_HASH=b18441a1ff607e10a989891a5462e627
    ```

    After the build completes successfully, the resulting binary will be located at:
    `tdesktop/out/Release/AyuGram`.

## Step 2: Prepare for the Flatpak Build

Now that we have the binary, we will prepare a dedicated directory for the Flatpak build.

1.  **Create a working directory:**
    Return to your parent directory and create a folder for the Flatpak build.

    ```bash
    # If you are inside the tdesktop directory, navigate out of it
    cd .. 
    mkdir ayugram-flatpak-build
    cd ayugram-flatpak-build
    ```

2.  **Copy the necessary files:**
    We need to copy three items from the `tdesktop` repository into this new directory:
    *   The built `AyuGram` binary.
    *   The `com.ayugram.desktop.yml` manifest and its resources (icons, .desktop file, metadata), which are located in the same folder.

    Execute the following commands from the `ayugram-flatpak-build` directory:

    ```bash
    # Copy the binary from the correct path
    cp ../tdesktop/out/Release/AyuGram .

    # Copy the manifest and all resources from the flatpak-files directory
    cp -r ../tdesktop/docs/assets/flatpak-files/* .
    ```

    After this, your `ayugram-flatpak-build` directory should have the following structure:
    ```
    .
    ├── AyuGram
    ├── com.ayugram.desktop.yml
    └── usr/
        └── share/
            ├── applications/
            ├── dbus-1/
            ├── icons/
            └── metainfo/
    ```

## Step 3: Build the Flatpak Package

Everything is now ready for the final step.

1.  **Install the GNOME SDK:**
    Our Flatpak uses the GNOME runtime. Ensure you have the corresponding SDK (Software Development Kit) installed.

    ```bash
    flatpak install --user org.gnome.Sdk//50
    ```
    *Note: The manifest uses runtime version `50`. If `flatpak` cannot find this version, make sure you have the Flathub repository enabled.*

You now have two build options.

### Option A: Build and Install into the System (for testing)

This method is ideal for quickly testing the application.

1.  **Run the build and installation:**

    ```bash
    flatpak-builder --user --install --force-clean build-dir com.ayugram.desktop.yml
    ```
    *   `--user`: Install for the current user.
    *   `--install`: Automatically install after building.
    *   `--force-clean`: Start with a clean build.
    *   `build-dir`: A temporary directory for the build.

    *Problem and Solution:* If you see a `Permission denied` or `Failure spawning rofiles-fuse` error, add the `--disable-rofiles-fuse` flag:
    ```bash
    flatpak-builder --disable-rofiles-fuse --user --install --force-clean build-dir com.ayugram.desktop.yml
    ```

2.  **Run the installed application:**

    ```bash
    flatpak run com.ayugram.desktop
    ```

### Option B: Build a Portable `.flatpak` File (for distribution)

This method creates a single file that can be distributed to other users for installation.

1.  **Clean up old artifacts (important!):**
    If you have previously attempted to build a bundle, delete the old repository directory to avoid errors.

    ```bash
    rm -rf repo
    ```

2.  **Build the application into a local repository:**

    ```bash
    flatpak-builder --repo=repo --force-clean build-dir com.ayugram.desktop.yml
    ```
    *   `--repo=repo`: Tells `flatpak-builder` to export the result into a directory named `repo`, creating a repository there.

    *Problem and Solution:* As with Option A, add the `--disable-rofiles-fuse` flag if you encounter a `rofiles-fuse` error.

3.  **Create the `.flatpak` bundle:**
    Now, let's package the contents of the `repo` repository into a single file.

    ```bash
    flatpak build-bundle repo ayugram-desktop-5.16.3.flatpak com.ayugram.desktop
    ```
    *   `repo`: The source (our local repository).
    *   `ayugram-desktop-5.16.3.flatpak`: The name of the final file (remember to update the version if necessary).
    *   `com.ayugram.desktop`: The ID of the application to be packaged.

As a result, the `ayugram-desktop-5.16.3.flatpak` file will appear in the current directory, ready for installation. It can be installed with the command:
```bash
flatpak install --user ayugram-desktop-5.16.3.flatpak
```

## CI workflows

- Stable release builds use `.github/workflows/flatpak-build.yml` and must receive an explicit upstream release tag through the `upstream_tag` workflow input.
- Dev builds use `.github/workflows/flatpak-dev.yml` and are started manually through `workflow_dispatch`. By default they build `upstream/dev` and publish a prerelease with a dev version suffix.
