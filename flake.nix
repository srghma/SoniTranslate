{
  description = "SoniTranslate development shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.python3
            # pkgs.pip
            pkgs.conda
            pkgs.git
            pkgs.ffmpeg
            pkgs.cudaPackages.cudatoolkit
            pkgs.onnxruntime
            # pkgs.pytorch
            # pkgs.torchaudio
            # pkgs.torchvision
          ];

          shellHook = ''
            echo "Activating SoniTranslate development environment..."
            # export OPENAI_API_KEY="your-api-key-here"
            conda create -n sonitr python=3.10 -y
            conda activate sonitr
            python -m pip install pip==23.1.2
            conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
            pip install -r requirements_base.txt -v
            pip install -r requirements_extra.txt -v
            pip install onnxruntime-gpu
          '';
        };
      }
    );
}
