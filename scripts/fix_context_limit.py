path = "analyze_manager.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Увеличиваем лимит чтения одного файла
if 'if len(content) > 10000:' in content:
    content = content.replace('if len(content) > 10000:', 'if len(content) > 50000:')
    print("✅ Increased per-file limit to 50k chars")

# Увеличиваем общий лимит в промпте
if '{full_text[:30000]}' in content:
    content = content.replace('{full_text[:30000]}', '{full_text[:120000]}')
    print("✅ Increased total prompt limit to 120k chars")
elif '{full_text[:35000]}' in content:
    content = content.replace('{full_text[:35000]}', '{full_text[:120000]}')
    print("✅ Increased total prompt limit to 120k chars")
else:
    print("⚠️ Could not find context limit string. Check manually.")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
