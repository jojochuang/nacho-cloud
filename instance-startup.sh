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
# http://stackoverflow.com/questions/3430330/best-way-to-make-a-shell-script-daemon
# nohup ./myscript 0<&- &>/dev/null &
# http://wiki.bash-hackers.org/howto/redirection_tutorial

# http://stackoverflow.com/questions/19233529/bash-sript-as-daemon
# setsid myscript.sh >/dev/null 2>&1 < /dev/null &
if [ $ROLE == "bootstrapper" ]; then
  setsid ./executable -lib.MApplication.bootstrapper me &
else
  BOOTSTRAPPER=$(curl http://metadata/computeMetadata/v1/instance/attributes/bootstrapper -H "X-Google-Metadata-Request: True")
  if [ $? -ne 0 ]; then
    echo "unable to get role metadata"
    exit
  fi
  setsid ./executable lib.MApplication.bootstrapper $BOOTSTRAPPER &
fi
#./executable
