echo "Installing ANARCI..."
cd ext/ANARCI
python setup.py install || true

cd -

echo "Installing Parapred..."
mkdir weights
wget https://github.com/alchemab/parapred-pytorch/raw/refs/tags/v1.0.2/parapred/weights/parapred_pytorch.h5 -P weights
cd ext/parapred-pytorch
make install
