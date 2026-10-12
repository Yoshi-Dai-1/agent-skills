# Material 3 Motion System Specifications

## 0. 主従関係（最重要）
- M3 Expressive の正本は **motion physics system（spring）** である。easing / duration は遷移用フォールバックおよび未移行チーム用であり、physics を代替しないこと。
- morph の対象定義は `02-shape-system.md`、コンポーネント別の適用は `06-component-specs.md` に従うこと。

## 1. Schemes と domains
- Schemes：`expressive`（弾みあり。hero moments・key interactions 用）/ `standard`（穏やか。chrome・lists・navigation の既定用）。製品全体は単一 scheme を既定とし、要点のみ個別に上書きすること。全体を expressive にすると混沌とする。
- Domains：`spatial`（位置・サイズ・回転・角丸。最終値をオーバーシュートして収束）/ `effects`（色・不透明度。オーバーシュート禁止）。
- Speeds：`fast`（小要素）/ `default`（大半）/ `slow`（全画面・大型）。
- Spring の三属性：`stiffness`（硬さ。高いほど速く収束）/ `damping`（減衰比。1.0 で臨界制動＝バウンスなし、低いほどオーバーシュート）/ `initial velocity`（初速。stiffness・damping と合成で所要時間を決める）。
- トークン命名：`md.sys.motion.spring.{fast,default,slow}.{spatial,effects}`。Compose では `MaterialTheme.motionScheme.*SpatialSpec / *EffectsSpec` を使うこと。ad-hoc な `spring(stiffness=..., dampingRatio=...)` を散布しないこと。

## 2. Web 換算表（springs が使えない場合の模倣曲線。正本値）
- `Expressive fast spatial`: curve 0.42, 1.67, 0.21, 0.90 / 350ms
- `Expressive default spatial`: curve 0.38, 1.21, 0.22, 1.00 / 500ms
- `Expressive slow spatial`: curve 0.39, 1.29, 0.35, 0.98 / 650ms
- `Expressive fast effects`: curve 0.31, 0.94, 0.34, 1.00 / 150ms
- `Expressive default effects`: curve 0.34, 0.80, 0.34, 1.00 / 200ms
- `Expressive slow effects`: curve 0.34, 0.88, 0.34, 1.00 / 300ms
- `Standard fast spatial`: curve 0.27, 1.06, 0.18, 1.00 / 350ms
- `Standard default spatial`: curve 0.27, 1.06, 0.18, 1.00 / 500ms
- `Standard slow spatial`: curve 0.27, 1.06, 0.18, 1.00 / 750ms
- `Standard fast/default/slow effects`: expressive effects と同値（150 / 200 / 300ms）
- 旧記述の「200〜500ms に収める」は誤り。slow spatial は 650〜750ms に達するため、上表を正本とすること。

## 3. Legacy easing（フォールバック専用）
- `Emphasized`: `cubic-bezier(0.2, 0.0, 0.0, 1.0)` / 500ms（画面内 begin〜end）
- `Emphasized decelerate`: `cubic-bezier(0.05, 0.7, 0.1, 1.0)` / 400ms（enter）
- `Emphasized accelerate`: `cubic-bezier(0.3, 0.0, 0.8, 0.15)` / 200ms（exit・復帰なしの印象）
- `Standard`: 300ms / `Standard decelerate`: 250ms / `Standard accelerate`: 200ms（小規模・utility 用および iOS / Web 等 Emphasized 非対応環境の fallback）
- 新規実装で easing を第一選択にしないこと。

## 4. 運用規則
- 位置・サイズ・角丸には spatial を、色・透明度には effects を使うこと。alpha に spatial（バウンスで範囲外）を、位置に effects（慣性なしで機械的）を当てないこと。
- Exit は `slowEffectsSpec` で一斉に終え、stagger を付けないこと（遅延知覚を避ける）。
- 100ms 級の micro interaction（toggle 等）にオーバーシュートは無駄である。fast effects または standard を使うこと。
- `prefers-reduced-motion` では morph・parallax・長時間 spring を抑制し、瞬時遷移または短い effects に切り替えること。
