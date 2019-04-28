# ptt_gossiping_summarizer
parse ptt gossiping article and summary by wordcloud and topic model(LDA)

## Usage:  
1. execute *`ptt_parser.py`* to create db & table (first time) and parse daily article  
2. execute *`gossipiing_daily_summarizer.py`* to get daily summary  
  
## Note:
*`ptt_parser.py`*: parse gossiping article menu and insert to DB `ptt.db` in table `gossiping_article_view`   
*`gossipiing_daily_summarizer.py`* : call `text_freq_analyst.py` to get wordcloud and apply LDA for textual analysis  
the result will in  `/summary_result_fig`  
  
`gossiping_article_view`:  

| PAGE  | DATE  | AUTHOR  | PUSH  | TITLE  | ARTICLE_URL  | RPT_DATETIME|
|------ |-------| --------|------ |--------| -------------|-------------|
| 39389 | 04/26  | ABCD5566 |3 | [問卦] 古埃及人長什麼樣子 |www.ptt.cc/bbs/Gossiping/M.1556208340.A.C28.html |2019-04-27 00:48:28|
| 39389 | 04/26  | ilove5566 |X2 | [臉書] 吳祥輝 Brian Wu |www.ptt.cc/bbs/Gossiping/M.1556208225.A.E7E.html |2019-04-27 00:48:28|
  
