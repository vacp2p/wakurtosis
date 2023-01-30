# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Kurtosis, naively assuming amd64
wget https://github.com/kurtosis-tech/kurtosis-cli-release-artifacts/releases/download/0.64.2/kurtosis-cli_0.64.2_linux_amd64.tar.gz
tar -xf kurtosis-cli_0.64.2_linux_amd64.tar.gz
mv kurtosis /usr/bin
rm -r scripts
rm kurtosis-cli_0.64.2_linux_amd64.tar.gz

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