---
name: agent-skill-craft
description: >-
  Use this skill when creating, auditing, or modifying an Agent Skill (a directory
  containing SKILL.md), authoring skill instructions, deciding a skill's file layout or
  progressive-disclosure structure, bundling scripts with a skill, or checking whether
  a skill triggers correctly. Apply it even when the user never says "skill" — for
  example 「このスキルの指示書きを直して」「SKILL.md を作って」「references をどう分ける
  べきか」「この skill が発動しない」, or 「この作業を毎回同じ手順でやりたい」. Also use it
  when auditing a skill for consistency, terminology, report accuracy, or spec
  compliance.
metadata:
  version: "3.0.0"
---

# Agent Skill Craft

Agent Skill（`SKILL.md` を含むディレクトリ）の設計・執筆・監査・改修・評価に関する実行プロセスを定義する。

## 概要と前提

- **ドメイン非依存**: あらゆる領域のスキルに同一のプロセスを適用する。特定領域の固有の規則を本プロトコルへ持ち込まないこと。
- **指示文と成果物の文体を分離する**: 詳細は `references/authoring.md` の 1 節に従う。
- **既存コンテキストの尊重**: すでに存在するコード、設定、正本データ、既存文書の構造を最優先で参照・継承し、重複や競合を発生させないこと。
- **判断の委譲**: AI エージェントが確定できる事項は決定し記録すること。意味・責任・範囲の確定を伴う事項は利用者の承認・確認を得ること。
- **各フェーズは到達すべき状態を定める。手順を 1 つに定めるものではない。** 同じ結果へ到達する別の手順があるときは、利用者と合意できる範囲で最も適切なものを選ぶ。順序や手順が固定されている箇所だけを厳密に指示する。

## 適用範囲

- 本スキルの範囲: Agent Skill の設計・執筆・監査・改修・評価、および評価設定の立案。
- 範囲外: 対象スキルの業務領域そのものの実装。対象スキルの実行時に行う業務処理には、Phase 4 が参照する実行時規律を適用する。
- **範囲外の入力を疑ったら、処理せずに理由を述べて利用者に確認する。**

## 段階的実行フェーズ（Phase Protocol）

各フェーズに「参照するファイル」と「読み込み条件」を明記する。条件に該当しないファイルは読み込まない。

### Phase 0: 対象の確定（Scope & Intent）

1. **対象の特定**: 作成／監査／改修の別、対象スキルの名称とディレクトリ、想定される利用タスクを確定すること。
2. **既存物の読み込み**: 対象ディレクトリが存在する場合は `SKILL.md`、`references/`、`scripts/`、`assets/`、`evals/` を全件読み込み、既存の設計を継承する。**`references/` がない場合は Phase 1 と Phase 2 で新規に作成し、`evals/` がない場合は Phase 3 の Layer C で新規に作成する。いずれも作成または改修の依頼に限る。監査のみの依頼では作成しない。**
3. **条件の確定**: 対象スキルのドメイン、出力物の読み手（機械可読か人間向けか）、実行環境（必要なツール・依存）を確定すること。
4. **評価方式の確定**: 出力が客観的に検証可能かを判断し、`references/evaluation.md` の 3.1 節（評価方式の選択）が示す A 機械的 assertion／B 利用者によるレビュー／C 両者のいずれか 1 つを選んで記録する。判断できない場合は利用者へ 1 行で確認する。**この判定に必要な 3.1 節のみを読み込む。**
5. **非限定の解釈**: 利用者の指示にある「など」「あらゆる」「すべての」などの非限定表現は、文字通り非限定と解釈し、範囲を狭めないこと。例示の列挙は代表例として扱い、限定とみなさないこと。範囲に疑義がある場合は狭めず、利用者に 1 行で確認すること。

### Phase 1: 公式仕様への適合設計（Specification Conformance）

1. `references/specification.md` を読み込み適用する。**このフェーズでは常に読み込む。** 仕様上の数値と規則の正本は `assets/agent-skills-spec.json` であり、記述と検証スクリプトはこの正本に対して行う。
2. 規定的要件（フロントマター、`name` と `description` の規則、ディレクトリ構成、ファイル参照規則、段階的開示の予算）を満たす設計を確定する。
3. 裁量的要件（参照ファイルの分割粒度、スクリプトの要否、アセットの要否）は、対象スキルの規模と利用頻度を勘案して判断し、判断根拠を記録する。**本スキルは分割の型を固定しない。**
4. `references/` を新規に作成する場合は、分割粒度と各ファイルに置く内容をここで設計し、Phase 2 でその設計どおりに作成する。

### Phase 2: 執筆（Authoring）

1. `references/authoring.md` を読み込み適用する。**`SKILL.md` 本文または参照ファイルを執筆・改稿する段階では常に読み込む。**
2. 対象スキルの落とし穴として実際に観測した事象を `SKILL.md` の Gotchas として蓄積する。
3. 出力形式が定まる場合は、テンプレートを用意する。置き場所は `references/authoring.md` の 8 節に従う。
4. 対象スキルの新規作成では、次のテンプレートを土台に複製する。複製したファイルは複製先から参照する。
   - `assets/skill-template.md` → 対象スキルの `SKILL.md`
   - `assets/reference-template.md` → 対象スキルの `references/` 配下の新規ファイル
   - `assets/evals-template.json` → 対象スキルの `evals/evals.json`
   - `assets/trigger-queries-template.json` → 対象スキルの `evals/trigger-queries.json`
5. **本スキルの `assets/` は、対象スキルの作成と改修にのみ使う。** 対象スキルの実行時には読み込まない。
6. **作業モードが監査のみの場合は、このフェーズでファイルを変更しない。** 違反箇所と修正案を報告するにとどめる。

### Phase 3: 検証（Verification）

1. **Layer A（機械走査）**: `python3 scripts/validate-skill.py <対象スキルディレクトリ> --vocabulary assets/vocabulary.json` を実行する。`skills-ref` コマンドが PATH にある場合は `skills-ref validate <対象スキルディレクトリ>` も実行する。機械走査と自己監査の守備範囲は `references/audit-protocol.md` の 5 節に従う。
   - 公式の検証ライブラリが利用できない場合は `skills-ref` による検証だけを省略し、省略の事実と理由を報告する。
   - Python 3 の実行環境がない場合はこの Layer 全体を省略し、Layer B で grep による全文検索を行う。検索対象は語族の全語と `assets/foreign-tokens.json` の全語とし、結果は引用付きで記録する。**grep では代替できない項目（言語の混在の検出、語彙の混在の検出）は、Layer B の報告で「対象外（検証手段の守備範囲外）」として明示する。**
2. **Layer B（証拠付き自己監査）**: `references/audit-protocol.md` を読み込み適用する。**この Layer では常に読み込む。** `scripts/audit-ledger.py` で未決済台帳を管理し、引用と行番号を伴わない指摘は採用しない。Layer A の検出結果も台帳に登録する。対象を全件走査し、未決済ゼロをもって終了する。
3. **Layer C（評価）**: `references/evaluation.md` を読み込み適用する。**トリガー評価は全件で必須**（`evals/trigger-queries.json`）、**出力評価は Phase 0 で決定した方式で必須**（`evals/evals.json`）。`evals/` がない場合の扱いは `references/evaluation.md` の 3 節に従う。

### Phase 4: 実行時規律の埋め込み（Runtime Protocol Embedding）

1. `references/execution-protocol.md`（実行時規律）を読み込み、対象スキルの `SKILL.md` へ実行時規律（計画の構造化と検証、対象全件の列挙と完了条件、範囲変更の事前合意、完了報告の 4 区分、手段の抽象化とフォールバック、同一の対象には同一の語、適用範囲外の実行）を反映する。**このフェーズは対象スキルの実行時規律を設計または改修する場合にのみ行う。**
2. **対象スキルがすでに同等の実行時規律を持つ場合は、既存の記述を参照で代替する。** 同じ内容を重複して書き足さない。
3. 反映後、Layer A と Layer B を再実行して、反映漏れがないことを確認する。再走査の範囲は `references/audit-protocol.md` の 2 節に従う。
4. 反映が対象スキルの `description` に及んだ場合は、トリガー評価も再実施する。

## 利用可能なスクリプト

- **`scripts/validate-skill.py`** — 公式仕様と運用ルールへの適合を検証する。終了コード `0`=適合、`1`=不適合、`2`=使用法エラー。
- **`scripts/audit-ledger.py`** — 監査の未決済台帳を管理する。終了コード `0`=成功、`1`=台帳エラー、`2`=使用法エラー。

## 語彙と表記の基準

- `references/vocabulary.md` を読み込み適用する。**語彙を使う記述では常に読み込む。**
- 正本の所在は 1 箇所にまとめる。公式仕様は `assets/agent-skills-spec.json`、語族は `assets/vocabulary.json`、言語の混在の検出を補助する語は `assets/foreign-tokens.json` である。
- 語族の混在の検証方法は `references/vocabulary.md` の 5 節に従う。
- 言語の混在の判定方法は `references/audit-protocol.md` の 7 節に、記述の重複および矛盾の候補の検出方法は 5 節 9 番に従う。

## Gotchas

実地運用で実際に踏んだ落とし穴のみを記述する。一般論や自明な事実は記述しない。

- **自己監査の反復**: 最終確認を反復すると、決済済みの指摘を新規として再掲し、監査が成立しなくなる。未決済台帳を持ち、決済済みは再掲しない。引用なしの指摘は採用しない。引用は監査時点の現行ファイルから取得し、記憶の文面で代替しない。
- **実行範囲の過剰表示**: 対象全体と宣言しながら一部のみを実施し、報告でも全体と書いた。宣言した対象と実施した対象を一致させ、完了条件には件数を明記する。
- **手段の固定**: 特定の手法を名指しすると、実行環境の変化で実行できなくなる。能力記述にしてフォールバックを定義する。
- **適用範囲の勝手な変更（縮小・拡大）**: 適用範囲を明示しないまま一般的知識から対象を推定すると、対象を意図せず縮小し、または対象外の入力を対象に加えて拡大する。適用範囲を冒頭に宣言する。
- **description の undertrigger**: description が「何をするか」だけの説明型になると発動しない。命令形に書き、利用者が領域名を明示しない場合の発動条件も列挙する。
- **成果物文体の誤適用**: 指示文向けの文体規則（読み手向けの解説を排するなど）を、対象スキルの成果物にも適用すると、文書作成系スキルの散文まで失われる。対象と成果物の文体を分ける。
- **言語の混在**: 基準言語と異なる言語の語が、引用として明示されずに文中に埋め込まれると、文として成立しなくなる。引用符・コードスパン・独立行・括弧で囲われた連続塊は意図された引用として許可する。判定方法は `references/audit-protocol.md` の 7 節に従う。
- **自己点検の不備**: 自分が作成した検証スクリプトは、自分のファイルも検証する。検証スクリプトが使う語彙データは検証対象から除外し、そのデータに混入があると誤検知する。

## よくある誤り

- 対象スキルの **指示文の文体**と**成果物の文体**を同一の規則で扱う。
- 機械走査で判定できる項目を自己監査だけで判定する、またはその逆を行う。守備範囲は `references/audit-protocol.md` の 5 節に従う。
- 対象スキルが **生成しない**成果物の形式を、対象スキル自身に要求する。
- 評価を省略した状態で「品質が向上した」と報告する。
