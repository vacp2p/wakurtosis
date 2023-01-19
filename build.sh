# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Kurtosis, naively assuming amd64
wget https://github.com/kurtosis-tech/kurtosis-cli-release-artifacts/releases/download/0.64.2/kurtosis-cli_0.64.2_linux_amd64.tar.gz
tar -xf kurtosis-cli_0.64.2_linux_amd64.tar.gz
mv kurtosis /usr/bin
rm -r scripts
rm kurtosis-cli_0.64.2_linux_amd64.tar.gz