USED_SERVICES=("codeartifact")

mkdir -p ./tmp/data/
for folder in "${USED_SERVICES[@]}"; do
    if [ -d "./pack/botocore/data/$folder" ]; then
        cp -r "./pack/botocore/data/$folder" "./tmp/data/"
    fi
done
cp -f ./pack/botocore/data/*.* ./tmp/data/
rm -rf ./pack/botocore/data
cp -r ./tmp/data ./pack/botocore/
rm -rf ./tmp/data
