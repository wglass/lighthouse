#!/usr/bin/env sh

IMAGE=$1
NAME=$2

ZK_LINK="--link zk01:zk01"
PARTNER_LINK=""

if [ "${IMAGE}" = "proxy" ]; then
   PARTNER_LINK="--link partnerapi:partnerapi"
fi

docker run --name ${NAME} --hostname ${NAME} ${ZK_LINK} ${PARTNER_LINK} -P -d lighthouse.examples.${IMAGE}
