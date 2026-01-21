# Known exceptions and what might be done about them

1. To order: has class `ohsk`, but has v instead of o

   ```
   corpus_id,entry_no,definition,present,present_1sg,imperfective,perfective,imperative,infinitive
   46,50,he/she is ordering it,atanvhsk,katanvhsk,atanvhsk,utanvhs,hatanvla,utanvhst
   ```

1. To brag: has class `sk-s-hihst`, but the sequence between the h-final root and the h in the class makes this fail (it wants immediate suffix `-ha` instead of `-a`). But we parse this root-final h as part of the stem-ending. Identifying this case seems very difficult.

   ```
   corpus_id,entry_no,definition,present,present_1sg,imperfective,perfective,imperative,infinitive
   100,104,he/she is bragging,atlvkwhsk,katlvkwahsk,atlvkwhsk,utlvkwhs,hatlvkwha,utlvkwhihst
   ```

1. To root out and to boil: these rows have a `tl` which has its vowel cut and is then deaffricated before a consonant. This leaves a hard to explain `tl -> tlh -> lh` transformation. These both take the `ih-vh` class.
   ```
   corpus_id,entry_no,definition,present,present_1sg,imperfective,perfective,imperative,infinitive
   311,318,it’s boiling,alitlih,,alitlihsk,ulitlvh,,ulilht
   1227,1278,he/she is rooting it out,khanahstetlih,tsinahstetlih,khanahstetlihsk,unhahstetlvh,hinhahstetla,unhahstelht
   ```
