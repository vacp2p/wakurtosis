# Run this if Kurtosis starts to crash because the gRPC 4Mb limit. 
du -h --max-depth=1 .git
git gc
git prune
du -h --max-depth=1 .git
