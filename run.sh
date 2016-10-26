#!/bin/bash
er pull hwy10/dnsbenchmark
docker run -p 50000:50000 -it hwy10/dnsbenchmark
