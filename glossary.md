# Glossary - Chou Mashin Eiyuuden Wataru: Another Step

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables: a JP form in the line needs one of its EN forms (`/` separates forms),
and Avoid spellings fail. The `## Speakers` table is matched exactly, on the speaker line only.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Wataru-kun, Sakuya-sama). Name order: Western (given name first) for kanji names
  (唄部千代子 = Chiyoko Utabe); katakana joke names joined with ・ keep the game's order (ヨメイリ・コウゾウ = Yomeiri Kozo).
- Romanisation source: no official English exists for this game or the 1997 series (D2): Hepburn without macrons.
  Names that pun on an English word or Western name take that spelling (D9: Warumonder, Warulilith, Watt, Thundar).
- Credits: English.
- Register (D10): a kids' comedy RPG. Natural, lively, playful English; light JP flavour (honorifics, -sama for
  royalty and the demon sisters' servants), no slang that dates it. Every pun or gag gets an English pun or gag.
- Sound effects (D10): English onomatopoeia, no asterisks, caps only for loud ones (BOOM!, Wham!, Zzz...).
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Style rules
- Punctuation map: 「」 -> "...", 『』 -> '...' (titles, quoted names), ・・・ -> ..., ！？ -> ?!, ！！ -> !!, ～/ー at
  a word end -> drawn-out letters ("Whoaaa!"), ♪ -> drop or "~". Plain ASCII only.
- Every box is 32 letters x 3 lines (two letters per 16x16 cell), the speaker line counts as one. Write the line
  breaks yourself (`\n`); the game does not wrap. A page that opens with `Name：` keeps a speaker line `Name:`.
- Choices: keep the JP line layout; a line that starts with N blank cells starts with 2N spaces (the hand cursor).
- Voice per character: docs/style-reference.md.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ワタル / 炎部ワタル | Wataru | | Wataru Homurabe, 10, the hero of 10,000 years ago (the game's Wataru) | |
| Ｇワタル | G-Wataru | | the game's Wataru when both appear | |
| ＴＶワタル | TV Wataru | | Wataru Ikusabe, the TV-series Wataru from the future | |
| 戦部 | Ikusabe | | | |
| 炎部 | Homurabe | | | |
| サクヤ / 忍部サクヤ | Sakuya | | Sakuya Shinobibe, ninja-clan head, Himiko's ancestor; posh princess speech (ですわ, おほほ) | |
| 忍部 | Shinobibe | | | |
| アラゴト / 剣部アラゴト | Aragoto | | Aragoto Tsurugibe, swordsman, Shibaraku's ancestor; pompous samurai | |
| 剣部 | Tsurugibe | | | |
| 龍神丸 | Ryujinmaru | | Wataru's mashin | Ryuujinmaru |
| ワルモンダー | Warumonder | | the demon ruler of Sokaizan | Warumonda |
| ワルリーヌ | Warurine | | the girl met in Ganbozukushi Village; secretly Warumonder's youngest daughter | Warulina / Warurinu |
| ワルトリン | Warutorin | | 3rd demon sister, 4th-layer boss | |
| ワルリリス | Warulilith | | 2nd demon sister, 5th-layer boss | Waruririsu |
| ワルジョ | Warujo | | eldest demon sister, 6th-layer boss; Aragoto's old flame | |
| オババ / 妖部オババ | Obaba | | Obaba Ayashibe, fortune-teller in Monja Village | |
| シバラク | Shibaraku | | | |
| ヒミコ | Himiko | | | |
| ヒシコ | Hishiko | | a Himiko knock-off | |
| ワタノレ | VVataru | | a counterfeit "Wataru" (ノレ for ル): keep the lookalike joke | Watanore |
| たくろー | Takuro | | | |
| ヨメイリ / ヨメイリ・コウゾウ | Yomeiri | | Yomeiri Kozo, Bride Village boss, chases Sakuya | |
| 唄部千代子 | Chiyoko Utabe | | | |
| ビリビリマン | Biribiri Man | | | |
| モロ・モロＱ / モロ・モロ | Moro Moro Q / Moro Moro | | film director, Extra Town | |
| オシシ | Oshishi | | Oshishi Mamomo, Character City | |
| メグ | Meg | | virtual idol, Idorian City | |
| カネワ / カネワ・アルゾウ | Kanewa | | Kanewa Aruzo, Ganbozukushi Village boss | |
| カネワローン | Kanewa Loans | | | |
| ワット | Watt | | Keiko Town | |
| サンダール | Thundar | | | Sandaru |
| ショタ郎 | Shotaro | | | |
| カール / カール・ジョンソン | Carl / Carl Johnson | | Gold Medalar's pilot | |
| ビル / ビル・ジョブス | Bill / Bill Jobs | | Mr. Illusion's pilot | |
| ミスター・イリュージョン | Mr. Illusion | | | |
| コサク | Kosaku | | | |
| キサク | Kisaku | | | |
| 銀之介 | Ginnosuke | | | |
| ナンパタロー | Flirty Taro | | | |
| 無気力タロー | Listless Taro | | | |
| ミサキ | Misaki | | | |
| ケンジ | Kenji | | | |
| アユカ | Ayuka | | | |
| フーミン | Fumin | | | |
| セーブおねえさん | Save Lady | | the cowgirl who saves the game (セーブ/西部 = save/western pun) | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 創界山 | Sokaizan | | the seven-layered mountain world | Soukaizan |
| 界層 / 界 | Layer | | 第一界 = the First Layer | |
| もんじゃ村 | Monja Village | | | |
| 龍神池 | Ryujin Pond | | | |
| 龍神町 | Ryujin Town | | Wataru's home town | |
| コンビニ村 | Konbini Village | | convenience-store village | |
| ガンボづくし村 | Ganbozukushi Village | | | |
| エキストラタウン | Extra Town | | | |
| キャラクターシティ | Character City | | | |
| ケイコータウン | Keiko Town | | | |
| シャンデリア城 | Chandelier Castle | | | |
| ビリビリタウン | Biribiri Town | | | |
| ビリビリ城 | Biribiri Castle | | | |
| エネルギー城 | Energy Castle | | | |
| アイドリアンシティ | Idorian City | | | |
| デジクロソフト | Digicrosoft | | | |
| サウンドエコー村 | Sound Echo Village | | | |
| ワルトリン城 | Warutorin Castle | | | |
| アスリート村 | Athlete Village | | | |
| コロッシアム | Colosseum | | | |
| アスレチック村 | Athletic Village | | | |
| ハナヨメ村 / 花嫁村 | Bride Village | | | |
| ハナヨメキャッスル | Bride Castle | | | |
| サビレータウン | Sabire Town | | | |
| 魔神湯治場 | Mashin Spa | | | |
| ムキリョク村 | Mukiryoku Village | | | |
| ワルモンダー城 | Warumonder Castle | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 魔神 | mashin | | the giant robots; lowercase as a common noun | Majin |
| 救世主 | Savior | | | Messiah |
| 登龍剣 | Toryuken | | the legendary sword | |
| もんペット | Monpet | | the pet monsters | |
| ボーリングバトル | Bowling Battle | | | |
| ＩＱバトル | IQ Battle | | | |
| 魔神バトル | Mashin Battle | | | |
| ワルワル | Waruwaru | | | |

## Speakers
| JP | EN |
|---|---|
| ワタル | Wataru |
| アラゴト | Aragoto |
| サクヤ | Sakuya |
| ワルリーヌ | Warurine |
| 龍神丸 | Ryujinmaru |
| Ｇワタル | G-Wataru |
| ＴＶワタル | TV Wataru |
| 両ワタル | Both Watarus |
| ワタルたち | Wataru & co. |
| ワタルとサクヤ | Wataru & Sakuya |
| ワタルとアラゴト | Wataru & Aragoto |
| アラゴトとワタル | Aragoto & Wataru |
| ワタルとワルリーヌ | Wataru & Warurine |
| アラゴトとワルリーヌ | Aragoto & Warurine |
| おねえさんとサクヤ | Young Woman & Sakuya |
| みんな | Everyone |
| 全員 | All |
| おじさん | Man |
| おばさん | Woman |
| おねえさん | Young Woman |
| おにいさん | Young Man |
| おじいさん | Old Man |
| じいさん | Old Man |
| おばあさん | Old Woman |
| おんなの子 | Girl |
| おとこの子 | Boy |
| はじめてのおとこの子 | First Boy |
| はじめてのおんなの子 | First Girl |
| 子供 | Kid |
| 村人 | Villager |
| 店の人 | Shopkeeper |
| 店員 | Clerk |
| 従業員 | Staff |
| 兵士 | Soldier |
| 警備員 | Guard |
| 部長 | Manager |
| 部長のムスコ | Manager's Son |
| ちょうろう | Elder |
| なぞのこえ | Mysterious Voice |
| ？？？ | ??? |
| オババ | Obaba |
| ワルトリン | Warutorin |
| ワルジョ | Warujo |
| ワルジョたち | Warujo & co. |
| ワルリリス | Warulilith |
| ワルモンダー | Warumonder |
| ワルモンダーの手下 | Warumonder's Minion |
| ワルリーヌの世話人 | Warurine's Caretaker |
| ヨメイリ | Yomeiri |
| シバラク | Shibaraku |
| ヒミコ | Himiko |
| たくろー | Takuro |
| たくろーのこえ | Takuro's Voice |
| 唄部千代子 | Chiyoko Utabe |
| ビル | Bill |
| ビリビリマン | Biribiri Man |
| モロ・モロＱ | Moro Moro Q |
| モロ・モロＱの手下 | Moro Moro Q's Minion |
| オシシ | Oshishi |
| メグ | Meg |
| カネワ | Kanewa |
| カネワローンの人 | Kanewa Loans Clerk |
| カール | Carl |
| ワット | Watt |
| サンダール | Thundar |
| ショタ郎 | Shotaro |
| コサク | Kosaku |
| キサク | Kisaku |
| 銀之介 | Ginnosuke |
| 魔神鍛冶 | Mashin Smith |
| セーブおねえさん | Save Lady |
| ファンクラブの会長 | Fan Club President |
| ファンの人 | Fan |
| モーレツなワタノレファン | Rabid VVataru Fan |
| おべんと娘 | Bento Girl |
| ナンパタロー | Flirty Taro |
| 無気力タロー | Listless Taro |
| コックみならい | Apprentice Cook |
| コックマスター | Master Chef |
| コントロールセンターの人 | Control Center Staff |
| 城の外からきこえるこえ | Voice Outside the Castle |
| カウントダウンのこえ | Countdown Voice |
| 女の子のひめい | Girl's Scream |
| おんなのこのひめい | Girl's Scream |
| ウンチクおばあさん | Know-It-All Granny |
| 若おくさん | Young Wife |
| 修理工Ａ | Mechanic A |
| 修理工Ｂ | Mechanic B |
| だらけた売り子 | Lazy Clerk |
| トラップしょくにん | Trap Maker |
| ミサキ | Misaki |
| ケンジ | Kenji |
| アユカ | Ayuka |
| フーミン | Fumin |
| リサ | Lisa |
| ヒロ | Hiro |
| はにぃ | Honey |
| わぁぼう | Waabo |
| 源ゴロー | Gengoro |
| ガッツさん | Guts-san |
| ワタルとサクヤ | Wataru & Sakuya |
| 作性のアラゴト | Aragoto |
| もんじゃ村での話 | Back in Monja Village |
| えびフライ | Fried Shrimp |

## Decisions from earlier batches
