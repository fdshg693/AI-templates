"""vault フロントマタースキーマ（SSOT）.

キー・型・許容値・配置パス・ステータスの意味は、このファイルだけに書く。
- 一覧文書 docs/vault-schema.md は gen_schema_doc.py がここから生成する（手で編集しない）。
- 読む側（validate / build_dashboard / build_index / check_entity / compact）は値のリストを書き写さず、ここから引く。
- 型・必須・許容値の誤りはエラー、運用ルール上の推奨違反は警告（``LINTS``）。

導入先のドメインに合わせて書き換える場所は「# --- 導入先で書き換える ---」の印を付けた定義。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable

# --- 導入先で書き換える ------------------------------------------------------

# 区分（scope）: 同じ構造を並列に持つ単位。vault/scopes/{scope}/ のフォルダ名と一致させる
SCOPES: dict[str, str] = {
    "life": "日常生活（仕事・趣味・健康などの分類は area で付ける）",
}

# 生活の領域。絞り込みとダッシュボードの小見出しに使う（自由な分類は tags）
AREAS: dict[str, str] = {
    "work": "仕事",
    "hobby": "趣味",
    "health": "健康・運動",
    "food": "食・お店",
    "home": "住まい・家事",
    "money": "お金",
    "learning": "学び",
    "people": "人づきあい",
}

KEY_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"  # entity-key（kebab-case）
CONTACT_KEY_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:_[a-z0-9]+(?:-[a-z0-9]+)*)+$"  # {org}_{name}


class StatusCategory(StrEnum):
    ACTIVE = "active"  # 続いている・これから・休止中
    CLOSED = "closed"  # 終わった
    EXCLUDED = "excluded"  # 二度とやらない


class ExclusionScope(StrEnum):
    """check_entity で「除外済み」と判定する範囲."""

    NONE = "none"
    SAME_SCOPE = "same_scope"  # 同じ scope でだけ除外（別 scope では参考提示）
    ALL_SCOPES = "all_scopes"  # 全 scope で除外


@dataclass(frozen=True)
class StatusMeta:
    label: str
    category: StatusCategory
    order: int  # ダッシュボードの並び順（小さいほど先）
    exclusion: ExclusionScope
    description: str


# --- 導入先で書き換える ---
ENTITY_STATUS: dict[str, StatusMeta] = {
    "ongoing": StatusMeta(
        "続けている", StatusCategory.ACTIVE, 0, ExclusionScope.NONE, "習慣・継続中の関心ごと"
    ),
    "trying": StatusMeta(
        "試し中",
        StatusCategory.ACTIVE,
        1,
        ExclusionScope.NONE,
        "始めたばかりで、続くか様子を見ている",
    ),
    "planned": StatusMeta(
        "これから",
        StatusCategory.ACTIVE,
        2,
        ExclusionScope.NONE,
        "やりたい・準備中で、まだ始めていない",
    ),
    "paused": StatusMeta(
        "休止中", StatusCategory.ACTIVE, 3, ExclusionScope.NONE, "時期・事情で一時的に止めている"
    ),
    "finished": StatusMeta(
        "終えた",
        StatusCategory.CLOSED,
        10,
        ExclusionScope.NONE,
        "区切りがついた（プロジェクト完了・読了など）",
    ),
    "quit": StatusMeta(
        "やめた", StatusCategory.CLOSED, 11, ExclusionScope.SAME_SCOPE, "自分の判断でやめた"
    ),
    "unavailable": StatusMeta(
        "続けられなくなった",
        StatusCategory.CLOSED,
        12,
        ExclusionScope.SAME_SCOPE,
        "外部要因（閉店・転居など）で続けられなくなった",
    ),
    "disliked": StatusMeta(
        "合わない",
        StatusCategory.EXCLUDED,
        20,
        ExclusionScope.ALL_SCOPES,
        "体質・好みに合わず、二度とやらない",
    ),
}

# 見送り台帳（archive.md）に畳める status。トリアージ由来のエントリは discarded
ARCHIVABLE_STATUS = ("quit", "unavailable", "disliked")
TRIAGE_STATUS = "discarded"
TRIAGE_EXCLUSION = ExclusionScope.SAME_SCOPE

EVENT_KINDS: dict[str, str] = {
    "log": "実施記録（やったこと）",
    "visit": "訪問・外出",
    "purchase": "購入",
    "talk": "相談・会話",
    "retro": "振り返り",
}

EVIDENCE_LEVELS: dict[str, str] = {
    "mentioned": "話に出ただけ・気になっている",
    "tried": "1〜数回やった",
    "habit": "習慣として続けている（続けていた）",
}

# ダッシュボードの「最近の出来事」に出す日数と、続いている対象のイベントログを要約（digests）に畳むまでの日数
RECENT_DAYS = 14
EVENT_DIGEST_DAYS = 30


def _interest_cell(d: dict[str, Any]) -> str:
    return "★" * d["interest"] if d.get("interest") else ""


def _cost_cell(d: dict[str, Any]) -> str:
    return f"{d['cost_monthly']:,}円" if d.get("cost_monthly") else ""


# ダッシュボードの「進行中の一覧」に足す題材固有の列: (見出し, entity の frontmatter → セルの文字列)
DASHBOARD_COLUMNS: tuple[tuple[str, Callable[[dict[str, Any]], str]], ...] = (
    ("頻度", lambda d: d.get("frequency") or ""),
    ("関心", _interest_cell),
    ("月額", _cost_cell),
)
# 「進行中の一覧」を小見出しで分ける entity の enum キー（分けないなら None）
DASHBOARD_GROUP_BY: str | None = "area"

# --- ここから下は汎用（導入先でもほぼそのまま使える） ------------------------

ACTION_TYPES: dict[str, str] = {
    "none": "タスクなし",
    "action_required": "自分側の対応が必要",
    "scheduled": "日時が確定した予定",
    "waiting": "相手側の返信・結果待ち",
}

EVENT_RESULTS: dict[str, str] = {
    "pending": "結果待ち",
    "positive": "前向き",
    "negative": "否定的",
    "not_applicable": "結果の無い記録",
}

CONTACT_STATUS: dict[str, str] = {
    "active": "やり取り中",
    "trusted": "信頼できる情報源",
    "declined": "やり取り終了",
    "blacklisted": "今後関わらない",
}

RATINGS: dict[str, str] = {
    "S": "極めて有益",
    "A": "有益",
    "B": "普通",
    "C": "やや難あり",
    "D": "有害",
}

VISIBILITY: dict[str, str] = {
    "public": "外部に出す文章の素材にしてよい",
    "internal": "内部の判断にだけ使う（外部に出す文章に引用しない）",
}

ARCHIVED_STATUS: dict[str, str] = {
    **{s: ENTITY_STATUS[s].label for s in ARCHIVABLE_STATUS},
    TRIAGE_STATUS: "トリアージで打ち切り",
}

ARCHIVE_REASON_MAX = 120  # 台帳の reason は「条件の言葉で 1〜2 文」
DIGEST_SUMMARY_MAX = 200  # digests の summary は「その期間の傾向を 2〜3 文」


# ---------------------------------------------------------------------------
# フィールド定義
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class F:
    """フロントマターの1キー.

    type: str | int | float | bool | date | due（日付 or 日時）| enum | list[str] | list[object]
    """

    name: str
    type: str
    desc: str
    required: bool = False
    choices: dict[str, Any] | None = None  # enum の許容値 → ラベル
    pattern: str | None = None
    min: float | None = None
    max: float | None = None
    max_len: int | None = None
    item: tuple["F", ...] = ()  # list[object] の要素のキー


@dataclass(frozen=True)
class Kind:
    """ドキュメント種別. 配置パス（glob）とキーの組."""

    name: str
    label: str
    globs: tuple[str, ...]
    fields: tuple[F, ...]
    key_field: str | None = None  # 配置フォルダ名（またはファイル名）と一致させるキー
    scope_field: str | None = None  # 配置先 scope と一致させるキー
    event_name: bool = False  # ファイル名を {YYYY-MM-DD}_{kind}.md とし date / kind と一致させる
    notes: tuple[str, ...] = field(default_factory=tuple)


_TRACKING = (
    F("updated_at", "date", "最終更新日", required=True),
    F("tags", "list[str]", "検索用タグ"),
)

_ENTITY = Kind(
    name="entity",
    label="エンティティ（1件1フォルダの index.md）",
    globs=("vault/scopes/*/entities/*/index.md",),
    key_field="key",
    scope_field="scope",
    fields=(
        F("title", "str", "名称（活動・場所・作品・プロジェクトなど）", required=True),
        F(
            "key",
            "str",
            "kebab-case のキー。フォルダ名と一致させる",
            required=True,
            pattern=KEY_PATTERN,
        ),
        F("aliases", "list[str]", "別名・略称・表記ゆれ（重複チェックの照合に使う）"),
        F("scope", "enum", "区分", required=True, choices=SCOPES),
        F("area", "enum", "生活の領域", required=True, choices=AREAS),
        F(
            "status",
            "enum",
            "現在の状態",
            required=True,
            choices={k: v.label for k, v in ENTITY_STATUS.items()},
        ),
        F("status_note", "str", "状態の補足（今どうしているか）"),
        F("close_reason", "str", "終えた・やめた理由（closed / excluded のとき必須）"),
        F("date", "date", "初回記録日", required=True),
        *_TRACKING,
        F("url", "str", "主となる参照先 URL（お店・サービスなど）"),
        F("evidence_level", "enum", "どこまで経験したか", choices=EVIDENCE_LEVELS),
        F(
            "verified_items",
            "list[str]",
            "分かっている好み・条件（本人が言った、または繰り返し記録されたこと）",
        ),
        F("unverified_items", "list[str]", "まだ分からないこと（次に本人に聞く）"),
        F("interest", "int", "本人の関心度（1〜5）。AI が推測で埋めない", min=1, max=5),
        F("frequency", "str", "頻度（例: 週3回、月1回）"),
        F("cost_monthly", "int", "月あたりの費用（円）", min=0),
        F("cost_note", "str", "費用の補足（年払い・1回ごと 等）"),
        F("contact", "str", "紹介元の contact-key（パスは書かない）", pattern=CONTACT_KEY_PATTERN),
        F("action_type", "enum", "直近アクションの種類", choices=ACTION_TYPES),
        F("next_action", "str", "直近アクションの内容"),
        F("next_due", "due", "期限・予定日時（YYYY-MM-DD / YYYY-MM-DD HH:MM）"),
        F(
            "digests",
            "list[object]",
            "要約に畳んだ古いイベントログ（compact.py --events が追記する）",
            item=(
                F("from", "date", "畳んだ期間の最初のイベントの日付", required=True),
                F("to", "date", "畳んだ期間の最後のイベントの日付", required=True),
                F("count", "int", "畳んだイベントログの件数", required=True, min=1),
                F(
                    "summary",
                    "str",
                    "その期間の傾向（2〜3 文）",
                    required=True,
                    max_len=DIGEST_SUMMARY_MAX,
                ),
            ),
        ),
    ),
)

_EVENT = Kind(
    name="event",
    label="イベントログ（1回1ファイル）",
    globs=("vault/scopes/*/entities/*/????-??-??_*.md", "vault/contacts/*/????-??-??_*.md"),
    event_name=True,
    fields=(
        F("date", "date", "実施日。ファイル名の日付と一致させる", required=True),
        F("kind", "enum", "種類。ファイル名の後半と一致させる", required=True, choices=EVENT_KINDS),
        F("title", "str", "表示名（標準ラベルから変えたいときだけ）"),
        F("result", "enum", "その回の結果", choices=EVENT_RESULTS),
        F("participants", "list[str]", "参加者・相手"),
        *_TRACKING,
    ),
)

_CONTACT = Kind(
    name="contact",
    label="コンタクト（情報をくれる人・経路。scope 横断）",
    globs=("vault/contacts/*/index.md",),
    key_field="contact_key",
    fields=(
        F("name", "str", "氏名・表示名", required=True),
        F(
            "contact_key",
            "str",
            "{org}_{name} 形式。フォルダ名と一致させる",
            required=True,
            pattern=CONTACT_KEY_PATTERN,
        ),
        F("org", "str", "所属"),
        F("scopes", "list[str]", "関わる scope"),
        F("status", "enum", "関係の状態", required=True, choices=CONTACT_STATUS),
        F("rating", "enum", "情報源としての評価", choices=RATINGS),
        F(
            "introduced",
            "list[object]",
            "紹介されたエンティティ",
            item=(
                F("name", "str", "名称", required=True),
                F("key", "str", "エンティティのキー（ログがあれば）", pattern=KEY_PATTERN),
                F("date", "date", "紹介日"),
                F("note", "str", "ログを作らなかった紹介の所感"),
            ),
        ),
        F("first_contact", "date", "初回接触日", required=True),
        *_TRACKING,
    ),
)

_TRIAGE = Kind(
    name="triage",
    label="トリアージ集約ログ（早期打ち切りをバッチ単位で1ファイル）",
    globs=("vault/scopes/*/triage/*.md",),
    scope_field="scope",
    fields=(
        F("date", "date", "実施日", required=True),
        F("scope", "enum", "区分", required=True, choices=SCOPES),
        F("topic", "str", "このバッチで何を見たか", required=True),
        F(
            "entries",
            "list[object]",
            "打ち切った対象（check_entity が照合する）",
            required=True,
            item=(
                F("name", "str", "名称", required=True),
                F("aliases", "list[str]", "別名"),
                F("reason", "str", "打ち切った理由（条件の言葉で）", required=True),
            ),
        ),
        *_TRACKING,
    ),
)

_ARCHIVE = Kind(
    name="archive",
    label="見送り台帳（終了したエンティティを 1 件数行に圧縮）",
    globs=("vault/scopes/*/archive.md",),
    scope_field="scope",
    fields=(
        F("scope", "enum", "区分", required=True, choices=SCOPES),
        F(
            "entries",
            "list[object]",
            "圧縮したエンティティ",
            item=(
                F("name", "str", "名称", required=True),
                F("key", "str", "元のキー（トリアージ由来なら無し）", pattern=KEY_PATTERN),
                F("aliases", "list[str]", "別名"),
                F("status", "enum", "元の status", required=True, choices=ARCHIVED_STATUS),
                F("closed_at", "date", "終了日", required=True),
                F(
                    "reason",
                    "str",
                    "何が合わなかったか（条件の言葉で 1〜2 文）",
                    required=True,
                    max_len=ARCHIVE_REASON_MAX,
                ),
                F("reconsider_if", "str", "何が変われば再検討してよいか"),
                F("contact", "str", "紹介元の contact-key", pattern=CONTACT_KEY_PATTERN),
            ),
        ),
        *_TRACKING,
    ),
)

_DASHBOARD = Kind(
    name="dashboard",
    label="ダッシュボード（一覧はマーカー間を自動生成）",
    globs=("vault/scopes/*/dashboard.md",),
    scope_field="scope",
    fields=(F("scope", "enum", "区分", required=True, choices=SCOPES), *_TRACKING),
)

_NOTE = Kind(
    name="note",
    label="ノート（判断軸・条件など、上記以外の frontmatter 付き文書）",
    globs=("vault/profile/**/*.md", "vault/scopes/*/README.md", "vault/scopes/*/criteria.md"),
    fields=(
        F("title", "str", "表題", required=True),
        F("visibility", "enum", "公開範囲", required=True, choices=VISIBILITY),
        *_TRACKING,
        F("source_file", "str", "派生（翻訳・要約）元のファイル。リポジトリルート相対"),
        F("source_updated_at", "date", "派生元の updated_at（同期した時点の値）"),
    ),
    notes=(
        "source_file を書いた文書は、派生元の updated_at が source_updated_at より新しいと警告になる（同期漏れ）。",
    ),
)

KINDS: dict[str, Kind] = {
    k.name: k for k in (_ENTITY, _EVENT, _CONTACT, _TRIAGE, _ARCHIVE, _DASHBOARD, _NOTE)
}


# ---------------------------------------------------------------------------
# 運用ルールの検査（警告）
# ---------------------------------------------------------------------------


def _lint_entity(d: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    lo, hi = d.get("score_min"), d.get("score_max")
    if (lo is None) != (hi is None):
        errors.append("score_min と score_max は両方記入するか、両方未記入にする")
    elif lo is not None and hi is not None:
        if lo > hi:
            errors.append("score_min が score_max より大きい")
        elif lo == hi and d.get("evidence_level") != "firsthand":
            warnings.append("score に幅が無い。一次情報で確かめるまでは幅を持たせる")
    cmin, cmax = d.get("cost_min"), d.get("cost_max")
    if isinstance(cmin, int) and isinstance(cmax, int) and cmin > cmax:
        errors.append("cost_min が cost_max より大きい")
    meta = ENTITY_STATUS.get(d.get("status", ""))
    if (
        meta
        and meta.category != StatusCategory.ACTIVE
        and d.get("status") != "adopted"
        and not d.get("close_reason")
    ):
        warnings.append(f"status={d['status']} なのに close_reason が無い")
    if d.get("action_type") in ("action_required", "scheduled") and not d.get("next_due"):
        warnings.append(f"action_type={d['action_type']} なのに next_due が無い")
    for i, g in enumerate(d.get("digests") or []):
        if g["from"] > g["to"]:
            errors.append(f"digests[{i}]: from が to より後")
    return errors, warnings


def _lint_event(d: dict[str, Any]) -> tuple[list[str], list[str]]:
    return [], (
        ["result が pending のまま。結果が出たら更新する"] if d.get("result") == "pending" else []
    )


LINTS: dict[str, Callable[[dict[str, Any]], tuple[list[str], list[str]]]] = {
    "entity": _lint_entity,
    "event": _lint_event,
}


def status_meta(status: str) -> StatusMeta:
    return ENTITY_STATUS[status]


def exclusion_of(status: str) -> ExclusionScope:
    if status == TRIAGE_STATUS:
        return TRIAGE_EXCLUSION
    return ENTITY_STATUS[status].exclusion
