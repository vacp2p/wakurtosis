# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

apt-get install -y jq

# Install the suitable kurtosis-cli
kurtosis_version=0.70.2
echo "deb [trusted=yes] https://apt.fury.io/kurtosis-tech/ /" | sudo tee /etc/apt/sources.list.d/kurtosis.list
sudo apt update
sudo apt-mark unhold kurtosis-cli
sudo apt install kurtosis-cli=$kurtosis_version
sudo apt-mark hold kurtosis-cli
sudo rm /etc/apt/sources.list.d/kurtosis.list

# Build the analysis docker image
cd analysis-module
sh ./build.sh
cd ..

# Build Gennet, WLS and Container-Proc monitoring docker images

cd gennet-module
sh ./build_docker.sh
cd ..

cd wls-module
docker build -t wls:0.0.1 .
cd ..

cd ./monitoring/container-proc
sh ./build.sh
cd ..

# Prepare container proc monitoring venv
python3 -m venv ./cproc-venv --without-pip
source ./cproc-venv/bin/activate   
curl https://bootstrap.pypa.io/get-pip.py | python
pip3 install -r ./monitoring/container-proc/requirements.txt
deactivate

git clone git@github.com:waku-org/go-waku.git
cd go-waku
docker build -t gowaku .
cd ..
rm -rf go-waku
