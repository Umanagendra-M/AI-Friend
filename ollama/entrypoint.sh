#!/bin/sh

ollama serve &
sleep 10 # Give ollama serve time to start
ollama pull llama3.2:latest
wait