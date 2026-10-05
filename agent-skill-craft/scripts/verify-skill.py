#!/usr/bin/env python3
import os
import re
import sys

FORBIDDEN_TERMS = [
    "ください", "〜せよ", "自動認識", "自動判定", "現在", "将来的に", "将来", "開発段階"
]

AMBIGUOUS_TERMS = [
    "適切に", "必要に応じて", "適宜", "なんでも"
]

def verify_skill(skill_dir):
    issues = []
    
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md_path):
        issues.append("[Error] SKILL.md が存在しません。")
        return issues
        
    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if not content.startswith("---"):
        issues.append("[Error] YAMLフロントマターが存在しません。")
    if "name:" not in content or "description:" not in content:
        issues.append("[Error] YAMLフロントマターに name または description が不足しています。")
        
    # Relative path checks
    links = re.findall(r'`(references/[^`]+)`', content) + re.findall(r'`(scripts/[^`]+)`', content) + re.findall(r'`(assets/[^`]+)`', content)
    for link in links:
        target_path = os.path.join(skill_dir, link)
        if not os.path.exists(target_path):
            issues.append(f"[Error] SKILL.md 内で参照されているファイル '{link}' が存在しません。")

    # Check SKILL.md and reference files (skipping meta-guideline files when checking forbidden terms)
    for root, _, files in os.walk(skill_dir):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, skill_dir)
                
                # We audit SKILL.md strictly for forbidden / ambiguous terms
                if file == "SKILL.md":
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                    
                    for term in FORBIDDEN_TERMS:
                        if term in text:
                            issues.append(f"[Warning] {relpath} に禁止語句/メタ単語 '{term}' が含まれています。")
                    
                    for term in AMBIGUOUS_TERMS:
                        if term in text:
                            issues.append(f"[Warning] {relpath} に曖昧表現 '{term}' が含まれています。")

    return issues

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = verify_skill(target)
    print(f"--- Skill Verification Results for {target} ---")
    if not results:
        print("✅ 検証パス: 違反項目は検出されませんでした。")
    else:
        for msg in results:
            print(msg)
