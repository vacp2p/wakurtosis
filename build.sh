# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install the suitable kurtosis-cli
kurtosis_version=0.66.2
echo "deb [trusted=yes] https://apt.fury.io/kurtosis-tech/ /" | sudo tee /etc/apt/sources.list.d/kurtosis.list
sudo apt update
sudo apt-mark unhold kurtosis-cli
sudo apt install kurtosis-cli=$kurtosis_version
sudo apt-mark hold kurtosis-cli
sudo rm /etc/apt/sources.list.d/kurtosis.list

# Build WSL and Gennet docker image
cd wsl-module
docker build -t wsl:0.0.1 .
cd ..

cd gennet-module
docker build -t gennet .
cd ..

git clone git@github.com:waku-org/go-waku.git
cd go-waku
docker build -t gowaku .
cd ..
rm -rf go-waku
