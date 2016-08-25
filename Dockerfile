############################################################
# Dockerfile for Smart DNS Containers
# Based on Ubuntu
# Author: Weiyue Huang <t-weh@microsoft.com>
############################################################

# Set the base image to Ubuntu
FROM ubuntu

# File Author / Maintainer
MAINTAINER Weiyue Huang

# Add the application resources URL
RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial main universe" >> /etc/apt/sources.list

# Update the sources list
RUN apt-get update

# Install dev tolls
# RUN apt-get install -y dnsutils tar curl vim wget dialog net-tools

# Install Python and Basic Python Tools
RUN apt-get install -y python python-dev python-distribute python-pip

#################
# DNS Benchmark
#################

ADD . /DNSBenchmark
WORKDIR /DNSBenchmark/script
RUN mkdir -p /DNSBenchmark/log
CMD python server.py
