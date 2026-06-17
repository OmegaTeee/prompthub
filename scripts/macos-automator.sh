API_KEY="sk-prompthub-default-001"
PROMPT="$1"

curl -s http://localhost:9090/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen3-4b-instruct-2507\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}]
  }" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
