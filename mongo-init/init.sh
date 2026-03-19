#!/usr/bin/env bash
set -e

echo "Waiting for MongoDB services..."
sleep 10

echo "Init config server replica set..."
mongosh mongodb://configsvr:27019 --eval '
rs.initiate({
  _id: "cfgRS",
  configsvr: true,
  members: [{ _id: 0, host: "configsvr:27019" }]
})'

echo "Init shard1 replica set..."
mongosh mongodb://shard1:27018 --eval '
rs.initiate({
  _id: "shard1RS",
  members: [{ _id: 0, host: "shard1:27018" }]
})'

echo "Init shard2 replica set..."
mongosh mongodb://shard2:27018 --eval '
rs.initiate({
  _id: "shard2RS",
  members: [{ _id: 0, host: "shard2:27018" }]
})'

echo "Waiting for replica sets..."
sleep 10

echo "Add shards and enable sharding..."
mongosh mongodb://mongos:27017 --eval '
sh.addShard("shard1RS/shard1:27018");
sh.addShard("shard2RS/shard2:27018");

sh.enableSharding("university");

db = db.getSiblingDB("university");

db.students.createIndex({ student_id: "hashed" });
sh.shardCollection("university.students", { student_id: "hashed" });

db.student_files.createIndex({ student_id: 1 });
db.student_files.createIndex({ file_id: 1 }, { unique: true });

sh.status();
'

echo "Mongo sharded cluster initialized."
