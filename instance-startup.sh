#!/bin/bash
LOGICAL_ID=$(curl http://metadata/computeMetadata/v1/instance/attributes/logical_id -H "X-Google-Metadata-Request: True")
if [ $? -ne 0 ]; then
  echo "unable to get logical id metadata"
  exit
fi
ROLE=$(curl http://metadata/computeMetadata/v1/instance/attributes/role -H "X-Google-Metadata-Request: True")
if [ $? -ne 0 ]; then
  echo "unable to get role metadata"
  exit
fi

#if [ $ROLE == "bootstrapper" ]; then
#
#else
#
#fi

if [ -e "executable" ]; then
  rm -f executable
fi
if [ -e "params.default" ]; then
  rm -f params.default
fi

BUCKET_PREFIX="gs://weichiu/nacho"${LOGICAL_ID}
echo $BUCKET_PREFIX
# download the executable
gsutil cp ${BUCKET_PREFIX}"/executable" executable
# download the parameter file
gsutil cp ${BUCKET_PREFIX}"/params.default" params.default

chmod a+x executable
./executable
