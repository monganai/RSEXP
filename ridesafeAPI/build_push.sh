docker build . -t monganai/ridesafeapi-exp:latest
docker push monganai/ridesafeapi-exp:latest
cd ../
cd K8S/
microk8s.kubectl delete -f rs-exp.yaml
microk8s.kubectl apply -f rs-exp.yaml
