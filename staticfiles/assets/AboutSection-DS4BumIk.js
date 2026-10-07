var ze=Object.defineProperty;var Be=(n,e,t)=>e in n?ze(n,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):n[e]=t;var b=(n,e,t)=>Be(n,typeof e!="symbol"?e+"":e,t);import{a as Me,u as Le}from"./vue-router-BO9Gj9LD.js";import{B as Ce}from"./Breadcrumbs-BCS2aIqD.js";import{_ as be,c as B,r as Pe,O as Ee,o as A,d as z,f as m,t as P,i as K,x as V,w as Ie,T as qe,F as Oe,e as De,s as Ze}from"./_plugin-vue_export-helper-kUGgy624.js";/* empty css                                                                    */function te(){return{async:!1,breaks:!1,extensions:null,gfm:!0,hooks:null,pedantic:!1,renderer:null,silent:!1,tokenizer:null,walkTokens:null}}var C=te();function xe(n){C=n}var M={exec:()=>null};function E(n){let e=[];return t=>{let s=Math.max(0,Math.min(3,t-1)),r=e[s];return r||(r=n(s),e[s]=r),r}}function d(n,e=""){let t=typeof n=="string"?n:n.source,s={replace:(r,l)=>{let a=typeof l=="string"?l:l.source;return a=a.replace(y.caret,"$1"),t=t.replace(r,a),s},getRegex:()=>new RegExp(t,e)};return s}var Qe=((n="")=>{try{return!!new RegExp("(?<=1)(?<!1)"+n)}catch{return!1}})(),y={codeRemoveIndent:/^(?: {1,4}| {0,3}\t)/gm,outputLinkReplace:/\\([\[\]])/g,indentCodeCompensation:/^(\s+)(?:```)/,beginningSpace:/^\s+/,endingHash:/#$/,startingSpaceChar:/^ /,endingSpaceChar:/ $/,nonSpaceChar:/[^ ]/,newLineCharGlobal:/\n/g,tabCharGlobal:/\t/g,multipleSpaceGlobal:/\s+/g,blankLine:/^[ \t]*$/,doubleBlankLine:/\n[ \t]*\n[ \t]*$/,blockquoteStart:/^ {0,3}>/,blockquoteSetextReplace:/\n {0,3}((?:=+|-+) *)(?=\n|$)/g,blockquoteSetextReplace2:/^ {0,3}>[ \t]?/gm,listReplaceNesting:/^ {1,4}(?=( {4})*[^ ])/g,listIsTask:/^\[[ xX]\] +\S/,listReplaceTask:/^\[[ xX]\] +/,listTaskCheckbox:/\[[ xX]\]/,anyLine:/\n.*\n/,hrefBrackets:/^<(.*)>$/,tableDelimiter:/[:|]/,tableAlignChars:/^\||\| *$/g,tableRowBlankLine:/\n[ \t]*$/,tableAlignRight:/^ *-+: *$/,tableAlignCenter:/^ *:-+: *$/,tableAlignLeft:/^ *:-+ *$/,startATag:/^<a /i,endATag:/^<\/a>/i,startPreScriptTag:/^<(pre|code|kbd|script)(\s|>)/i,endPreScriptTag:/^<\/(pre|code|kbd|script)(\s|>)/i,startAngleBracket:/^</,endAngleBracket:/>$/,pedanticHrefTitle:/^([^'"]*[^\s])\s+(['"])(.*)\2/,unicodeAlphaNumeric:/[\p{L}\p{N}]/u,escapeTest:/[&<>"']/,escapeReplace:/[&<>"']/g,escapeTestNoEncode:/[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/,escapeReplaceNoEncode:/[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/g,caret:/(^|[^\[])\^/g,percentDecode:/%25/g,findPipe:/\|/g,splitPipe:/ \|/,slashPipe:/\\\|/g,carriageReturn:/\r\n|\r/g,spaceLine:/^ +$/gm,notSpaceStart:/^\S*/,endingNewline:/\n$/,listItemRegex:n=>new RegExp(`^( {0,3}${n})((?:[	 ][^\\n]*)?(?:\\n|$))`),nextBulletRegex:E(n=>new RegExp(`^ {0,${n}}(?:[*+-]|\\d{1,9}[.)])((?:[ 	][^\\n]*)?(?:\\n|$))`)),hrRegex:E(n=>new RegExp(`^ {0,${n}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`)),fencesBeginRegex:E(n=>new RegExp(`^ {0,${n}}(?:\`\`\`|~~~)`)),headingBeginRegex:E(n=>new RegExp(`^ {0,${n}}#`)),htmlBeginRegex:E(n=>new RegExp(`^ {0,${n}}<(?:[a-z].*>|!--)`,"i")),blockquoteBeginRegex:E(n=>new RegExp(`^ {0,${n}}>`))},Ne=/^(?:[ \t]*(?:\n|$))+/,He=/^((?: {4}| {0,3}\t)[^\n]+(?:\n(?:[ \t]*(?:\n|$))*)?)+/,je=/^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/,Q=/^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/,Ge=/^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/,ne=/ {0,3}(?:[*+-]|\d{1,9}[.)])/,me=/^(?!bull |blockCode|fences|blockquote|heading|html|table)((?:.|\n(?!\s*?\n|bull |blockCode|fences|blockquote|heading|html|table))+?)\n {0,3}(=+|-+) *(?:\n+|$)/,we=d(me).replace(/bull/g,ne).replace(/blockCode/g,/(?: {4}| {0,3}\t)/).replace(/fences/g,/ {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g,/ {0,3}>/).replace(/heading/g,/ {0,3}#{1,6}(?:\s|$)/).replace(/html/g,/ {0,3}<[^\n>]+>\n/).replace(/\|table/g,"").getRegex(),Fe=d(me).replace(/bull/g,ne).replace(/blockCode/g,/(?: {4}| {0,3}\t)/).replace(/fences/g,/ {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g,/ {0,3}>/).replace(/heading/g,/ {0,3}#{1,6}(?:\s|$)/).replace(/html/g,/ {0,3}<[^\n>]+>\n/).replace(/table/g,/ {0,3}\|?(?:[:\- ]*\|)+[\:\- ]*\n/).getRegex(),re=/^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table|[ \t]+\n)[^\n]+)*)/,Ue=/^[^\n]+/,se=/(?!\s*\])(?:\\[\s\S]|[^\[\]\\])+/,Xe=d(/^ {0,3}\[(label)\]: *(?:\n[ \t]*)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n[ \t]*)?| *\n[ \t]*)(title))? *(?:\n+|$)/).replace("label",se).replace("title",/(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/).getRegex(),We=d(/^(bull)([ \t][^\n]*?)?(?:\n|$)/).replace(/bull/g,ne).getRegex(),U="address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul",ie=/<!--(?:-?>|[\s\S]*?(?:-->|$))/,Ke=d("^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n*|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>[^\\n]*\\n*|$)|<![A-Z][\\s\\S]*?(?:>[^\\n]*\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>[^\\n]*\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$))","i").replace("comment",ie).replace("tag",U).replace("attribute",/ +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex(),ye=n=>d(re).replace("hr",Q).replace("heading"," {0,3}#{1,6}(?:\\s|$)").replace("|lheading","").replace("|table","").replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~~~)[^\\n]*\\n").replace("list",n).replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",U).getRegex(),Ve=ye(/ {0,3}(?:[*+-]|1[.)])[ \t]+[^ \t\n]/),Je=ye(/ {0,3}(?:[*+-]|\d{1,9}[.)])(?:[ \t]|\n|$)/),Ye=d(/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/).replace("paragraph",Je).getRegex(),le={blockquote:Ye,code:He,def:Xe,fences:je,heading:Ge,hr:Q,html:Ke,lheading:we,list:We,newline:Ne,paragraph:Ve,table:M,text:Ue},he=d("^ *([^\\n ].*)\\n {0,3}((?:\\| *)?:?-+:? *(?:\\| *:?-+:? *)*(?:\\| *)?)(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)").replace("hr",Q).replace("heading"," {0,3}#{1,6}(?:\\s|$)").replace("blockquote"," {0,3}>").replace("code","(?: {4}| {0,3}	)[^\\n]").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~~~)[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",U).getRegex(),et={...le,lheading:Fe,table:he,paragraph:d(re).replace("hr",Q).replace("heading"," {0,3}#{1,6}(?:\\s|$)").replace("|lheading","").replace("table",he).replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~~~)[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)])[ \\t]+[^ \\t\\n]").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",U).getRegex()},tt={...le,html:d(`^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:"[^"]*"|'[^']*'|\\s[^'"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))`).replace("comment",ie).replace(/tag/g,"(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(),def:/^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/,heading:/^(#{1,6})(.*)(?:\n+|$)/,fences:M,lheading:/^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/,paragraph:d(re).replace("hr",Q).replace("heading",` *#{1,6} *[^
]`).replace("lheading",we).replace("|table","").replace("blockquote"," {0,3}>").replace("|fences","").replace("|list","").replace("|html","").replace("|tag","").getRegex()},nt=/^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/,rt=/^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/,Se=/^( {2,}|\\)\n(?!\s*$)/,st=/^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/,I=/[\p{P}\p{S}]/u,X=/[\s\p{P}\p{S}]/u,ae=/[^\s\p{P}\p{S}]/u,it=d(/^((?![*_])punctSpace)/,"u").replace(/punctSpace/g,X).getRegex(),Re=/(?!~)[\p{P}\p{S}]/u,lt=/(?!~)[\s\p{P}\p{S}]/u,at=/(?:[^\s\p{P}\p{S}]|~)/u,ot=d(/link|precode-code|html/,"g").replace("link",/\[(?:[^\[\]`]|(?<a>`+)[^`]+\k<a>(?!`))*?\]\((?:\\[\s\S]|[^\\\(\)]|\((?:\\[\s\S]|[^\\\(\)])*\))*\)/).replace("precode-",Qe?"(?<!`)()":"(^^|[^`])").replace("code",/(?<b>`+)[^`]+\k<b>(?!`)/).replace("html",/<(?! )[^<>]*?>/).getRegex(),$e=/^(?:\*+(?:((?!\*)punct)|([^\s*]))?)|^_+(?:((?!_)punct)|([^\s_]))?/,ct=d($e,"u").replace(/punct/g,I).getRegex(),ht=d($e,"u").replace(/punct/g,Re).getRegex(),Te="^[^_*]*?__[^_*]*?\\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\\*)punct(\\*+)(?=[\\s]|$)|notPunctSpace(\\*+)(?!\\*)(?=punctSpace|$)|(?!\\*)punctSpace(\\*+)(?=notPunctSpace)|[\\s](\\*+)(?!\\*)(?=punct)|(?!\\*)punct(\\*+)(?!\\*)(?=punct)|notPunctSpace(\\*+)(?=notPunctSpace)",pt=d(Te,"gu").replace(/notPunctSpace/g,ae).replace(/punctSpace/g,X).replace(/punct/g,I).getRegex(),ut=d(Te,"gu").replace(/notPunctSpace/g,at).replace(/punctSpace/g,lt).replace(/punct/g,Re).getRegex(),gt=d("^[^_*]*?\\*\\*[^_*]*?_[^_*]*?(?=\\*\\*)|[^_]+(?=[^_])|(?!_)punct(_+)(?=[\\s]|$)|notPunctSpace(_+)(?!_)(?=punctSpace|$)|(?!_)punctSpace(_+)(?=notPunctSpace)|[\\s](_+)(?!_)(?=punct)|(?!_)punct(_+)(?!_)(?=punct)","gu").replace(/notPunctSpace/g,ae).replace(/punctSpace/g,X).replace(/punct/g,I).getRegex(),kt=d(/^~~?(?:((?!~)punct)|[^\s~])/,"u").replace(/punct/g,I).getRegex(),dt="^[^~]+(?=[^~])|(?!~)punct(~~?)(?=[\\s]|$)|notPunctSpace(~~?)(?!~)(?=punctSpace|$)|(?!~)punctSpace(~~?)(?=notPunctSpace)|[\\s](~~?)(?!~)(?=punct)|(?!~)punct(~~?)(?!~)(?=punct)|notPunctSpace(~~?)(?=notPunctSpace)",ft=d(dt,"gu").replace(/notPunctSpace/g,ae).replace(/punctSpace/g,X).replace(/punct/g,I).getRegex(),bt=d(/\\(punct)/,"gu").replace(/punct/g,I).getRegex(),xt=d(/^<(scheme:[^\s\x00-\x1f<>]*|email)>/).replace("scheme",/[a-zA-Z][a-zA-Z0-9+.-]{1,31}/).replace("email",/[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/).getRegex(),mt=d(ie).replace("(?:-->|$)","-->").getRegex(),wt=d("^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>").replace("comment",mt).replace("attribute",/\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/).getRegex(),j=/(?:\[(?:\\[\s\S]|[^\[\]\\])*\]|\\[\s\S]|`+(?!`)[^`]*?`+(?!`)|``+(?=\])|[^\[\]\\`])*?/,yt=d(/^!?\[(label)\]\(\s*(href)(?:(?:[ \t]+(?:\n[ \t]*)?|\n[ \t]*)(title))?\s*\)/).replace("label",j).replace("href",/<(?:\\.|[^\n<>\\])+>|[^ \t\n\x00-\x1f]+|(?=\))/).replace("title",/"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/).getRegex(),_e=d(/^!?\[(label)\]\[(ref)\]/).replace("label",j).replace("ref",se).getRegex(),ve=d(/^!?\[(ref)\](?:\[\])?/).replace("ref",se).getRegex(),St=d("reflink|nolink(?!\\()","g").replace("reflink",_e).replace("nolink",ve).getRegex(),pe=/[hH][tT][tT][pP][sS]?|[fF][tT][pP]/,oe={_backpedal:M,anyPunctuation:bt,autolink:xt,blockSkip:ot,br:Se,code:rt,del:M,delLDelim:M,delRDelim:M,emStrongLDelim:ct,emStrongRDelimAst:pt,emStrongRDelimUnd:gt,escape:nt,link:yt,nolink:ve,punctuation:it,reflink:_e,reflinkSearch:St,tag:wt,text:st,url:M},Rt={...oe,link:d(/^!?\[(label)\]\((.*?)\)/).replace("label",j).getRegex(),reflink:d(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label",j).getRegex()},J={...oe,emStrongRDelimAst:ut,emStrongLDelim:ht,delLDelim:kt,delRDelim:ft,url:d(/^((?:protocol):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/).replace("protocol",pe).replace("email",/[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/).getRegex(),_backpedal:/(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/,del:/^(~~?)(?=[^\s~])((?:\\[\s\S]|[^\\])*?(?:\\[\s\S]|[^\s~\\]))\1(?=[^~]|$)/,text:d(/^(`+|~+|[^`~])(?:(?=[`~])|(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|protocol:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/).replace("protocol",pe).getRegex()},$t={...J,br:d(Se).replace("{2,}","*").getRegex(),text:d(J.text).replace("\\b_","\\b_| {2,}\\n").replace(/\{2,\}/g,"*").getRegex()},N={normal:le,gfm:et,pedantic:tt},D={normal:oe,gfm:J,breaks:$t,pedantic:Rt},Tt={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"},ue=n=>Tt[n];function _(n,e){if(e){if(y.escapeTest.test(n))return n.replace(y.escapeReplace,ue)}else if(y.escapeTestNoEncode.test(n))return n.replace(y.escapeReplaceNoEncode,ue);return n}function ge(n){try{n=encodeURI(n).replace(y.percentDecode,"%")}catch{return null}return n}function ke(n,e){var l;let t=n.replace(y.findPipe,(a,o,i)=>{let p=!1,h=o;for(;--h>=0&&i[h]==="\\";)p=!p;return p?"|":" |"}),s=t.split(y.splitPipe),r=0;if(s[0].trim()||s.shift(),s.length>0&&!((l=s.at(-1))!=null&&l.trim())&&s.pop(),e)if(s.length>e)s.splice(e);else for(;s.length<e;)s.push("");for(;r<s.length;r++)s[r]=s[r].trim().replace(y.slashPipe,"|");return s}function v(n,e,t){let s=n.length;if(s===0)return"";let r=0;for(;r<s&&n.charAt(s-r-1)===e;)r++;return n.slice(0,s-r)}function de(n){let e=n.split(`
`),t=e.length-1;for(;t>=0&&y.blankLine.test(e[t]);)t--;return e.length-t<=2?n:e.slice(0,t+1).join(`
`)}function _t(n,e){if(n.indexOf(e[1])===-1)return-1;let t=0;for(let s=0;s<n.length;s++)if(n[s]==="\\")s++;else if(n[s]===e[0])t++;else if(n[s]===e[1]&&(t--,t<0))return s;return t>0?-2:-1}function vt(n,e=0){let t=e,s="";for(let r of n)if(r==="	"){let l=4-t%4;s+=" ".repeat(l),t+=l}else s+=r,t++;return s}function fe(n,e,t,s,r){let l=e.href,a=e.title||null,o=n[1].replace(r.other.outputLinkReplace,"$1");s.state.inLink=!0;let i={type:n[0].charAt(0)==="!"?"image":"link",raw:t,href:l,title:a,text:o,tokens:s.inlineTokens(o)};return s.state.inLink=!1,i}function At(n,e,t){let s=n.match(t.other.indentCodeCompensation);if(s===null)return e;let r=s[1];return e.split(`
`).map(l=>{let a=l.match(t.other.beginningSpace);if(a===null)return l;let[o]=a;return o.length>=r.length?l.slice(r.length):l}).join(`
`)}var G=class{constructor(n){b(this,"options");b(this,"rules");b(this,"lexer");this.options=n||C}space(n){let e=this.rules.block.newline.exec(n);if(e&&e[0].length>0)return{type:"space",raw:e[0]}}code(n){let e=this.rules.block.code.exec(n);if(e){let t=this.options.pedantic?e[0]:de(e[0]),s=t.replace(this.rules.other.codeRemoveIndent,"");return{type:"code",raw:t,codeBlockStyle:"indented",text:s}}}fences(n){let e=this.rules.block.fences.exec(n);if(e){let t=e[0],s=At(t,e[3]||"",this.rules);return{type:"code",raw:t,lang:e[2]?e[2].trim().replace(this.rules.inline.anyPunctuation,"$1"):e[2],text:s}}}heading(n){let e=this.rules.block.heading.exec(n);if(e){let t=e[2].trim();if(this.rules.other.endingHash.test(t)){let s=v(t,"#");(this.options.pedantic||!s||this.rules.other.endingSpaceChar.test(s))&&(t=s.trim())}return{type:"heading",raw:v(e[0],`
`),depth:e[1].length,text:t,tokens:this.lexer.inline(t)}}}hr(n){let e=this.rules.block.hr.exec(n);if(e)return{type:"hr",raw:v(e[0],`
`)}}blockquote(n){let e=this.rules.block.blockquote.exec(n);if(e){let t=v(e[0],`
`).split(`
`),s="",r="",l=[];for(;t.length>0;){let a=!1,o=[],i;for(i=0;i<t.length;i++)if(this.rules.other.blockquoteStart.test(t[i]))o.push(t[i]),a=!0;else if(!a)o.push(t[i]);else break;t=t.slice(i);let p=o.join(`
`),h=p.replace(this.rules.other.blockquoteSetextReplace,`
    $1`).replace(this.rules.other.blockquoteSetextReplace2,"");s=s?`${s}
${p}`:p,r=r?`${r}
${h}`:h;let g=this.lexer.state.top;if(this.lexer.state.top=!0,this.lexer.blockTokens(h,l,!0),this.lexer.state.top=g,t.length===0)break;let c=l.at(-1);if((c==null?void 0:c.type)==="code")break;if((c==null?void 0:c.type)==="blockquote"){let k=c,u=k.raw+`
`+t.join(`
`),x=this.blockquote(u);l[l.length-1]=x,s=s.substring(0,s.length-k.raw.length)+x.raw,r=r.substring(0,r.length-k.text.length)+x.text;break}else if((c==null?void 0:c.type)==="list"){let k=c,u=k.raw+`
`+t.join(`
`),x=this.list(u);l[l.length-1]=x,s=s.substring(0,s.length-c.raw.length)+x.raw,r=r.substring(0,r.length-k.raw.length)+x.raw,t=u.substring(l.at(-1).raw.length).split(`
`);continue}}return{type:"blockquote",raw:s,tokens:l,text:r}}}list(n){let e=this.rules.block.list.exec(n);if(e){let t=e[1].trim(),s=t.length>1,r={type:"list",raw:"",ordered:s,start:s?+t.slice(0,-1):"",loose:!1,items:[]};t=s?`\\d{1,9}\\${t.slice(-1)}`:`\\${t}`,this.options.pedantic&&(t=s?t:"[*+-]");let l=this.rules.other.listItemRegex(t),a=!1;for(;n;){let i=!1,p="",h="";if(!(e=l.exec(n))||this.rules.block.hr.test(n))break;p=e[0],n=n.substring(p.length);let g=vt(e[2].split(`
`,1)[0],e[1].length),c=n.split(`
`,1)[0],k=!g.trim(),u=0;if(this.options.pedantic?(u=2,h=g.trimStart()):k?u=e[1].length+1:(u=g.search(this.rules.other.nonSpaceChar),u=u>4?1:u,h=g.slice(u),u+=e[1].length),k&&this.rules.other.blankLine.test(c)&&(p+=c+`
`,n=n.substring(c.length+1),i=!0),!i){let x=this.rules.other.nextBulletRegex(u),w=this.rules.other.hrRegex(u),R=this.rules.other.fencesBeginRegex(u),S=this.rules.other.headingBeginRegex(u),q=this.rules.other.htmlBeginRegex(u),Ae=this.rules.other.blockquoteBeginRegex(u);for(;n;){let W=n.split(`
`,1)[0],O;if(c=W,this.options.pedantic?(c=c.replace(this.rules.other.listReplaceNesting,"  "),O=c):O=c.replace(this.rules.other.tabCharGlobal,"    "),R.test(c)||S.test(c)||q.test(c)||Ae.test(c)||x.test(c)||w.test(c))break;if(O.search(this.rules.other.nonSpaceChar)>=u||!c.trim())h+=`
`+O.slice(u);else{if(k||g.replace(this.rules.other.tabCharGlobal,"    ").search(this.rules.other.nonSpaceChar)>=4||R.test(g)||S.test(g)||w.test(g))break;h+=`
`+c}k=!c.trim(),p+=W+`
`,n=n.substring(W.length+1),g=O.slice(u)}}r.loose||(a?r.loose=!0:this.rules.other.doubleBlankLine.test(p)&&(a=!0)),r.items.push({type:"list_item",raw:p,task:!!this.options.gfm&&this.rules.other.listIsTask.test(h),loose:!1,text:h,tokens:[]}),r.raw+=p}let o=r.items.at(-1);if(o)o.raw=o.raw.trimEnd(),o.text=o.text.trimEnd();else return;r.raw=r.raw.trimEnd();for(let i of r.items){this.lexer.state.top=!1,i.tokens=this.lexer.blockTokens(i.text,[]);let p=i.tokens[0];if(i.task&&((p==null?void 0:p.type)==="text"||(p==null?void 0:p.type)==="paragraph")){i.text=i.text.replace(this.rules.other.listReplaceTask,""),p.raw=p.raw.replace(this.rules.other.listReplaceTask,""),p.text=p.text.replace(this.rules.other.listReplaceTask,"");for(let g=this.lexer.inlineQueue.length-1;g>=0;g--)if(this.rules.other.listIsTask.test(this.lexer.inlineQueue[g].src)){this.lexer.inlineQueue[g].src=this.lexer.inlineQueue[g].src.replace(this.rules.other.listReplaceTask,"");break}let h=this.rules.other.listTaskCheckbox.exec(i.raw);if(h){let g={type:"checkbox",raw:h[0]+" ",checked:h[0]!=="[ ]"};i.checked=g.checked,r.loose?i.tokens[0]&&["paragraph","text"].includes(i.tokens[0].type)&&"tokens"in i.tokens[0]&&i.tokens[0].tokens?(i.tokens[0].raw=g.raw+i.tokens[0].raw,i.tokens[0].text=g.raw+i.tokens[0].text,i.tokens[0].tokens.unshift(g)):i.tokens.unshift({type:"paragraph",raw:g.raw,text:g.raw,tokens:[g]}):i.tokens.unshift(g)}}else i.task&&(i.task=!1);if(!r.loose){let h=i.tokens.filter(c=>c.type==="space"),g=h.length>0&&h.some(c=>this.rules.other.anyLine.test(c.raw));r.loose=g}}if(r.loose)for(let i of r.items){i.loose=!0;for(let p of i.tokens)p.type==="text"&&(p.type="paragraph")}return r}}html(n){let e=this.rules.block.html.exec(n);if(e){let t=de(e[0]);return{type:"html",block:!0,raw:t,pre:e[1]==="pre"||e[1]==="script"||e[1]==="style",text:t}}}def(n){let e=this.rules.block.def.exec(n);if(e){let t=e[1].toLowerCase().replace(this.rules.other.multipleSpaceGlobal," "),s=e[2]?e[2].replace(this.rules.other.hrefBrackets,"$1").replace(this.rules.inline.anyPunctuation,"$1"):"",r=e[3]?e[3].substring(1,e[3].length-1).replace(this.rules.inline.anyPunctuation,"$1"):e[3];return{type:"def",tag:t,raw:v(e[0],`
`),href:s,title:r}}}table(n){var a;let e=this.rules.block.table.exec(n);if(!e||!this.rules.other.tableDelimiter.test(e[2]))return;let t=ke(e[1]),s=e[2].replace(this.rules.other.tableAlignChars,"").split("|"),r=(a=e[3])!=null&&a.trim()?e[3].replace(this.rules.other.tableRowBlankLine,"").split(`
`):[],l={type:"table",raw:v(e[0],`
`),header:[],align:[],rows:[]};if(t.length===s.length){for(let o of s)this.rules.other.tableAlignRight.test(o)?l.align.push("right"):this.rules.other.tableAlignCenter.test(o)?l.align.push("center"):this.rules.other.tableAlignLeft.test(o)?l.align.push("left"):l.align.push(null);for(let o=0;o<t.length;o++)l.header.push({text:t[o],tokens:this.lexer.inline(t[o]),header:!0,align:l.align[o]});for(let o of r)l.rows.push(ke(o,l.header.length).map((i,p)=>({text:i,tokens:this.lexer.inline(i),header:!1,align:l.align[p]})));return l}}lheading(n){let e=this.rules.block.lheading.exec(n);if(e){let t=e[1].trim();return{type:"heading",raw:v(e[0],`
`),depth:e[2].charAt(0)==="="?1:2,text:t,tokens:this.lexer.inline(t)}}}paragraph(n){let e=this.rules.block.paragraph.exec(n);if(e){let t=e[1].charAt(e[1].length-1)===`
`?e[1].slice(0,-1):e[1];return{type:"paragraph",raw:e[0],text:t,tokens:this.lexer.inline(t)}}}text(n){let e=this.rules.block.text.exec(n);if(e)return{type:"text",raw:e[0],text:e[0],tokens:this.lexer.inline(e[0])}}escape(n){let e=this.rules.inline.escape.exec(n);if(e)return{type:"escape",raw:e[0],text:e[1]}}tag(n){let e=this.rules.inline.tag.exec(n);if(e)return!this.lexer.state.inLink&&this.rules.other.startATag.test(e[0])?this.lexer.state.inLink=!0:this.lexer.state.inLink&&this.rules.other.endATag.test(e[0])&&(this.lexer.state.inLink=!1),!this.lexer.state.inRawBlock&&this.rules.other.startPreScriptTag.test(e[0])?this.lexer.state.inRawBlock=!0:this.lexer.state.inRawBlock&&this.rules.other.endPreScriptTag.test(e[0])&&(this.lexer.state.inRawBlock=!1),{type:"html",raw:e[0],inLink:this.lexer.state.inLink,inRawBlock:this.lexer.state.inRawBlock,block:!1,text:e[0]}}link(n){let e=this.rules.inline.link.exec(n);if(e){let t=e[2].trim();if(!this.options.pedantic&&this.rules.other.startAngleBracket.test(t)){if(!this.rules.other.endAngleBracket.test(t))return;let l=v(t.slice(0,-1),"\\");if((t.length-l.length)%2===0)return}else{let l=_t(e[2],"()");if(l===-2)return;if(l>-1){let a=(e[0].indexOf("!")===0?5:4)+e[1].length+l;e[2]=e[2].substring(0,l),e[0]=e[0].substring(0,a).trim(),e[3]=""}}let s=e[2],r="";if(this.options.pedantic){let l=this.rules.other.pedanticHrefTitle.exec(s);l&&(s=l[1],r=l[3])}else r=e[3]?e[3].slice(1,-1):"";return s=s.trim(),this.rules.other.startAngleBracket.test(s)&&(this.options.pedantic&&!this.rules.other.endAngleBracket.test(t)?s=s.slice(1):s=s.slice(1,-1)),fe(e,{href:s&&s.replace(this.rules.inline.anyPunctuation,"$1"),title:r&&r.replace(this.rules.inline.anyPunctuation,"$1")},e[0],this.lexer,this.rules)}}reflink(n,e){let t;if((t=this.rules.inline.reflink.exec(n))||(t=this.rules.inline.nolink.exec(n))){let s=(t[2]||t[1]).replace(this.rules.other.multipleSpaceGlobal," "),r=e[s.toLowerCase()];if(!r){let l=t[0].charAt(0);return{type:"text",raw:l,text:l}}return fe(t,r,t[0],this.lexer,this.rules)}}emStrong(n,e,t=""){let s=this.rules.inline.emStrongLDelim.exec(n);if(!(!s||!s[1]&&!s[2]&&!s[3]&&!s[4]||s[4]&&t.match(this.rules.other.unicodeAlphaNumeric))&&(!(s[1]||s[3])||!t||this.rules.inline.punctuation.exec(t))){let r=[...s[0]].length-1,l,a,o=r,i=0,p=s[0][0]==="*"?this.rules.inline.emStrongRDelimAst:this.rules.inline.emStrongRDelimUnd;for(p.lastIndex=0,e=e.slice(-1*n.length+r);(s=p.exec(e))!==null;){if(l=s[1]||s[2]||s[3]||s[4]||s[5]||s[6],!l)continue;if(a=[...l].length,s[3]||s[4]){o+=a;continue}else if((s[5]||s[6])&&r%3&&!((r+a)%3)){i+=a;continue}if(o-=a,o>0)continue;a=Math.min(a,a+o+i);let h=[...s[0]][0].length,g=n.slice(0,r+s.index+h+a);if(Math.min(r,a)%2){let k=g.slice(1,-1);return{type:"em",raw:g,text:k,tokens:this.lexer.inlineTokens(k)}}let c=g.slice(2,-2);return{type:"strong",raw:g,text:c,tokens:this.lexer.inlineTokens(c)}}}}codespan(n){let e=this.rules.inline.code.exec(n);if(e){let t=e[2].replace(this.rules.other.newLineCharGlobal," "),s=this.rules.other.nonSpaceChar.test(t),r=this.rules.other.startingSpaceChar.test(t)&&this.rules.other.endingSpaceChar.test(t);return s&&r&&(t=t.substring(1,t.length-1)),{type:"codespan",raw:e[0],text:t}}}br(n){let e=this.rules.inline.br.exec(n);if(e)return{type:"br",raw:e[0]}}del(n,e,t=""){let s=this.rules.inline.delLDelim.exec(n);if(s&&(!s[1]||!t||this.rules.inline.punctuation.exec(t))){let r=[...s[0]].length-1,l,a,o=r,i=this.rules.inline.delRDelim;for(i.lastIndex=0,e=e.slice(-1*n.length+r);(s=i.exec(e))!==null;){if(l=s[1]||s[2]||s[3]||s[4]||s[5]||s[6],!l||(a=[...l].length,a!==r))continue;if(s[3]||s[4]){o+=a;continue}if(o-=a,o>0)continue;a=Math.min(a,a+o);let p=[...s[0]][0].length,h=n.slice(0,r+s.index+p+a),g=h.slice(r,-r);return{type:"del",raw:h,text:g,tokens:this.lexer.inlineTokens(g)}}}}autolink(n){let e=this.rules.inline.autolink.exec(n);if(e){let t,s;return e[2]==="@"?(t=e[1],s="mailto:"+t):(t=e[1],s=t),{type:"link",raw:e[0],text:t,href:s,tokens:[{type:"text",raw:t,text:t}]}}}url(n){var t;let e;if(e=this.rules.inline.url.exec(n)){let s,r;if(e[2]==="@")s=e[0],r="mailto:"+s;else{let l;do l=e[0],e[0]=((t=this.rules.inline._backpedal.exec(e[0]))==null?void 0:t[0])??"";while(l!==e[0]);s=e[0],e[1]==="www."?r="http://"+e[0]:r=e[0]}return{type:"link",raw:e[0],text:s,href:r,tokens:[{type:"text",raw:s,text:s}]}}}inlineText(n){let e=this.rules.inline.text.exec(n);if(e){let t=this.lexer.state.inRawBlock;return{type:"text",raw:e[0],text:e[0],escaped:t}}}},$=class Y{constructor(e){b(this,"tokens");b(this,"options");b(this,"state");b(this,"inlineQueue");b(this,"tokenizer");this.tokens=[],this.tokens.links=Object.create(null),this.options=e||C,this.options.tokenizer=this.options.tokenizer||new G,this.tokenizer=this.options.tokenizer,this.tokenizer.options=this.options,this.tokenizer.lexer=this,this.inlineQueue=[],this.state={inLink:!1,inRawBlock:!1,top:!0};let t={other:y,block:N.normal,inline:D.normal};this.options.pedantic?(t.block=N.pedantic,t.inline=D.pedantic):this.options.gfm&&(t.block=N.gfm,this.options.breaks?t.inline=D.breaks:t.inline=D.gfm),this.tokenizer.rules=t}static get rules(){return{block:N,inline:D}}static lex(e,t){return new Y(t).lex(e)}static lexInline(e,t){return new Y(t).inlineTokens(e)}lex(e){e=e.replace(y.carriageReturn,`
`),this.blockTokens(e,this.tokens);for(let t=0;t<this.inlineQueue.length;t++){let s=this.inlineQueue[t];this.inlineTokens(s.src,s.tokens)}return this.inlineQueue=[],this.tokens}blockTokens(e,t=[],s=!1){var l,a,o;this.tokenizer.lexer=this,this.options.pedantic&&(e=e.replace(y.tabCharGlobal,"    ").replace(y.spaceLine,""));let r=1/0;for(;e;){if(e.length<r)r=e.length;else{this.infiniteLoopError(e.charCodeAt(0));break}let i;if((a=(l=this.options.extensions)==null?void 0:l.block)!=null&&a.some(h=>(i=h.call({lexer:this},e,t))?(e=e.substring(i.raw.length),t.push(i),!0):!1))continue;if(i=this.tokenizer.space(e)){e=e.substring(i.raw.length);let h=t.at(-1);i.raw.length===1&&h!==void 0?h.raw+=`
`:t.push(i);continue}if(i=this.tokenizer.code(e)){e=e.substring(i.raw.length);let h=t.at(-1);(h==null?void 0:h.type)==="paragraph"||(h==null?void 0:h.type)==="text"?(h.raw+=(h.raw.endsWith(`
`)?"":`
`)+i.raw,h.text+=`
`+i.text,this.inlineQueue.at(-1).src=h.text):t.push(i);continue}if(i=this.tokenizer.fences(e)){e=e.substring(i.raw.length),t.push(i);continue}if(i=this.tokenizer.heading(e)){e=e.substring(i.raw.length),t.push(i);continue}if(i=this.tokenizer.hr(e)){e=e.substring(i.raw.length),t.push(i);continue}if(i=this.tokenizer.blockquote(e)){e=e.substring(i.raw.length),t.push(i);continue}if(i=this.tokenizer.list(e)){e=e.substring(i.raw.length),t.push(i);continue}if(i=this.tokenizer.html(e)){e=e.substring(i.raw.length),t.push(i);continue}if(i=this.tokenizer.def(e)){e=e.substring(i.raw.length);let h=t.at(-1);(h==null?void 0:h.type)==="paragraph"||(h==null?void 0:h.type)==="text"?(h.raw+=(h.raw.endsWith(`
`)?"":`
`)+i.raw,h.text+=`
`+i.raw,this.inlineQueue.at(-1).src=h.text):this.tokens.links[i.tag]||(this.tokens.links[i.tag]={href:i.href,title:i.title},t.push(i));continue}if(i=this.tokenizer.table(e)){e=e.substring(i.raw.length),t.push(i);continue}if(i=this.tokenizer.lheading(e)){e=e.substring(i.raw.length),t.push(i);continue}let p=e;if((o=this.options.extensions)!=null&&o.startBlock){let h=1/0,g=e.slice(1),c;this.options.extensions.startBlock.forEach(k=>{c=k.call({lexer:this},g),typeof c=="number"&&c>=0&&(h=Math.min(h,c))}),h<1/0&&h>=0&&(p=e.substring(0,h+1))}if(this.state.top&&(i=this.tokenizer.paragraph(p))){let h=t.at(-1);s&&(h==null?void 0:h.type)==="paragraph"?(h.raw+=(h.raw.endsWith(`
`)?"":`
`)+i.raw,h.text+=`
`+i.text,this.inlineQueue.pop(),this.inlineQueue.at(-1).src=h.text):t.push(i),s=p.length!==e.length,e=e.substring(i.raw.length);continue}if(i=this.tokenizer.text(e)){e=e.substring(i.raw.length);let h=t.at(-1);(h==null?void 0:h.type)==="text"?(h.raw+=(h.raw.endsWith(`
`)?"":`
`)+i.raw,h.text+=`
`+i.text,this.inlineQueue.pop(),this.inlineQueue.at(-1).src=h.text):t.push(i);continue}if(e){this.infiniteLoopError(e.charCodeAt(0));break}}return this.state.top=!0,t}inline(e,t=[]){return this.inlineQueue.push({src:e,tokens:t}),t}inlineTokens(e,t=[]){var o,i,p,h,g;this.tokenizer.lexer=this;let s=e;if(this.tokens.links){let c=Object.keys(this.tokens.links);c.length>0&&(s=s.replace(this.tokenizer.rules.inline.reflinkSearch,k=>c.includes(k.slice(k.lastIndexOf("[")+1,-1))?"["+"a".repeat(k.length-2)+"]":k))}s=s.replace(this.tokenizer.rules.inline.anyPunctuation,"++"),s=s.replace(this.tokenizer.rules.inline.blockSkip,(c,k,u)=>{let x=u?u.length:0;return c.slice(0,x)+"["+"a".repeat(c.length-x-2)+"]"}),s=((i=(o=this.options.hooks)==null?void 0:o.emStrongMask)==null?void 0:i.call({lexer:this},s))??s;let r=!1,l="",a=1/0;for(;e;){if(e.length<a)a=e.length;else{this.infiniteLoopError(e.charCodeAt(0));break}r||(l=""),r=!1;let c;if((h=(p=this.options.extensions)==null?void 0:p.inline)!=null&&h.some(u=>(c=u.call({lexer:this},e,t))?(e=e.substring(c.raw.length),t.push(c),!0):!1))continue;if(c=this.tokenizer.escape(e)){e=e.substring(c.raw.length),t.push(c);continue}if(c=this.tokenizer.tag(e)){e=e.substring(c.raw.length),t.push(c);continue}if(c=this.tokenizer.link(e)){e=e.substring(c.raw.length),t.push(c);continue}if(c=this.tokenizer.reflink(e,this.tokens.links)){e=e.substring(c.raw.length);let u=t.at(-1);c.type==="text"&&(u==null?void 0:u.type)==="text"?(u.raw+=c.raw,u.text+=c.text):t.push(c);continue}if(c=this.tokenizer.emStrong(e,s,l)){e=e.substring(c.raw.length),t.push(c);continue}if(c=this.tokenizer.codespan(e)){e=e.substring(c.raw.length),t.push(c);continue}if(c=this.tokenizer.br(e)){e=e.substring(c.raw.length),t.push(c);continue}if(c=this.tokenizer.del(e,s,l)){e=e.substring(c.raw.length),t.push(c);continue}if(c=this.tokenizer.autolink(e)){e=e.substring(c.raw.length),t.push(c);continue}if(!this.state.inLink&&(c=this.tokenizer.url(e))){e=e.substring(c.raw.length),t.push(c);continue}let k=e;if((g=this.options.extensions)!=null&&g.startInline){let u=1/0,x=e.slice(1),w;this.options.extensions.startInline.forEach(R=>{w=R.call({lexer:this},x),typeof w=="number"&&w>=0&&(u=Math.min(u,w))}),u<1/0&&u>=0&&(k=e.substring(0,u+1))}if(c=this.tokenizer.inlineText(k)){e=e.substring(c.raw.length),c.raw.slice(-1)!=="_"&&(l=c.raw.slice(-1)),r=!0;let u=t.at(-1);(u==null?void 0:u.type)==="text"?(u.raw+=c.raw,u.text+=c.text):t.push(c);continue}if(e){this.infiniteLoopError(e.charCodeAt(0));break}}return t}infiniteLoopError(e){let t="Infinite loop on byte: "+e;if(this.options.silent)console.error(t);else throw new Error(t)}},F=class{constructor(n){b(this,"options");b(this,"parser");this.options=n||C}space(n){return""}code({text:n,lang:e,escaped:t}){var l;let s=(l=(e||"").match(y.notSpaceStart))==null?void 0:l[0],r=n.replace(y.endingNewline,"")+`
`;return s?'<pre><code class="language-'+_(s)+'">'+(t?r:_(r,!0))+`</code></pre>
`:"<pre><code>"+(t?r:_(r,!0))+`</code></pre>
`}blockquote({tokens:n}){return`<blockquote>
${this.parser.parse(n)}</blockquote>
`}html({text:n}){return n}def(n){return""}heading({tokens:n,depth:e}){return`<h${e}>${this.parser.parseInline(n)}</h${e}>
`}hr(n){return`<hr>
`}list(n){let e=n.ordered,t=n.start,s="";for(let a=0;a<n.items.length;a++){let o=n.items[a];s+=this.listitem(o)}let r=e?"ol":"ul",l=e&&t!==1?' start="'+t+'"':"";return"<"+r+l+`>
`+s+"</"+r+`>
`}listitem(n){return`<li>${this.parser.parse(n.tokens)}</li>
`}checkbox({checked:n}){return"<input "+(n?'checked="" ':"")+'disabled="" type="checkbox"> '}paragraph({tokens:n}){return`<p>${this.parser.parseInline(n)}</p>
`}table(n){let e="",t="";for(let r=0;r<n.header.length;r++)t+=this.tablecell(n.header[r]);e+=this.tablerow({text:t});let s="";for(let r=0;r<n.rows.length;r++){let l=n.rows[r];t="";for(let a=0;a<l.length;a++)t+=this.tablecell(l[a]);s+=this.tablerow({text:t})}return s&&(s=`<tbody>${s}</tbody>`),`<table>
<thead>
`+e+`</thead>
`+s+`</table>
`}tablerow({text:n}){return`<tr>
${n}</tr>
`}tablecell(n){let e=this.parser.parseInline(n.tokens),t=n.header?"th":"td";return(n.align?`<${t} align="${n.align}">`:`<${t}>`)+e+`</${t}>
`}strong({tokens:n}){return`<strong>${this.parser.parseInline(n)}</strong>`}em({tokens:n}){return`<em>${this.parser.parseInline(n)}</em>`}codespan({text:n}){return`<code>${_(n,!0)}</code>`}br(n){return"<br>"}del({tokens:n}){return`<del>${this.parser.parseInline(n)}</del>`}link({href:n,title:e,tokens:t}){let s=this.parser.parseInline(t),r=ge(n);if(r===null)return s;n=r;let l='<a href="'+n+'"';return e&&(l+=' title="'+_(e)+'"'),l+=">"+s+"</a>",l}image({href:n,title:e,text:t,tokens:s}){s&&(t=this.parser.parseInline(s,this.parser.textRenderer));let r=ge(n);if(r===null)return _(t);n=r;let l=`<img src="${n}" alt="${_(t)}"`;return e&&(l+=` title="${_(e)}"`),l+=">",l}text(n){return"tokens"in n&&n.tokens?this.parser.parseInline(n.tokens):"escaped"in n&&n.escaped?n.text:_(n.text)}},ce=class{strong({text:n}){return n}em({text:n}){return n}codespan({text:n}){return n}del({text:n}){return n}html({text:n}){return n}text({text:n}){return n}link({text:n}){return""+n}image({text:n}){return""+n}br(){return""}checkbox({raw:n}){return n}},T=class ee{constructor(e){b(this,"options");b(this,"renderer");b(this,"textRenderer");this.options=e||C,this.options.renderer=this.options.renderer||new F,this.renderer=this.options.renderer,this.renderer.options=this.options,this.renderer.parser=this,this.textRenderer=new ce}static parse(e,t){return new ee(t).parse(e)}static parseInline(e,t){return new ee(t).parseInline(e)}parse(e){var s,r;this.renderer.parser=this;let t="";for(let l=0;l<e.length;l++){let a=e[l];if((r=(s=this.options.extensions)==null?void 0:s.renderers)!=null&&r[a.type]){let i=a,p=this.options.extensions.renderers[i.type].call({parser:this},i);if(p!==!1||!["space","hr","heading","code","table","blockquote","list","html","def","paragraph","text"].includes(i.type)){t+=p||"";continue}}let o=a;switch(o.type){case"space":{t+=this.renderer.space(o);break}case"hr":{t+=this.renderer.hr(o);break}case"heading":{t+=this.renderer.heading(o);break}case"code":{t+=this.renderer.code(o);break}case"table":{t+=this.renderer.table(o);break}case"blockquote":{t+=this.renderer.blockquote(o);break}case"list":{t+=this.renderer.list(o);break}case"checkbox":{t+=this.renderer.checkbox(o);break}case"html":{t+=this.renderer.html(o);break}case"def":{t+=this.renderer.def(o);break}case"paragraph":{t+=this.renderer.paragraph(o);break}case"text":{t+=this.renderer.text(o);break}default:{let i='Token with "'+o.type+'" type was not found.';if(this.options.silent)return console.error(i),"";throw new Error(i)}}}return t}parseInline(e,t=this.renderer){var r,l;this.renderer.parser=this;let s="";for(let a=0;a<e.length;a++){let o=e[a];if((l=(r=this.options.extensions)==null?void 0:r.renderers)!=null&&l[o.type]){let p=this.options.extensions.renderers[o.type].call({parser:this},o);if(p!==!1||!["escape","html","link","image","strong","em","codespan","br","del","text"].includes(o.type)){s+=p||"";continue}}let i=o;switch(i.type){case"escape":{s+=t.text(i);break}case"html":{s+=t.html(i);break}case"link":{s+=t.link(i);break}case"image":{s+=t.image(i);break}case"checkbox":{s+=t.checkbox(i);break}case"strong":{s+=t.strong(i);break}case"em":{s+=t.em(i);break}case"codespan":{s+=t.codespan(i);break}case"br":{s+=t.br(i);break}case"del":{s+=t.del(i);break}case"text":{s+=t.text(i);break}default:{let p='Token with "'+i.type+'" type was not found.';if(this.options.silent)return console.error(p),"";throw new Error(p)}}}return s}},H,Z=(H=class{constructor(n){b(this,"options");b(this,"block");this.options=n||C}preprocess(n){return n}postprocess(n){return n}processAllTokens(n){return n}emStrongMask(n){return n}provideLexer(n=this.block){return n?$.lex:$.lexInline}provideParser(n=this.block){return n?T.parse:T.parseInline}},b(H,"passThroughHooks",new Set(["preprocess","postprocess","processAllTokens","emStrongMask"])),b(H,"passThroughHooksRespectAsync",new Set(["preprocess","postprocess","processAllTokens"])),H),zt=class{constructor(...n){b(this,"defaults",te());b(this,"options",this.setOptions);b(this,"parse",this.parseMarkdown(!0));b(this,"parseInline",this.parseMarkdown(!1));b(this,"Parser",T);b(this,"Renderer",F);b(this,"TextRenderer",ce);b(this,"Lexer",$);b(this,"Tokenizer",G);b(this,"Hooks",Z);this.use(...n)}walkTokens(n,e){var s,r;let t=[];for(let l of n)switch(t=t.concat(e.call(this,l)),l.type){case"table":{let a=l;for(let o of a.header)t=t.concat(this.walkTokens(o.tokens,e));for(let o of a.rows)for(let i of o)t=t.concat(this.walkTokens(i.tokens,e));break}case"list":{let a=l;t=t.concat(this.walkTokens(a.items,e));break}default:{let a=l;(r=(s=this.defaults.extensions)==null?void 0:s.childTokens)!=null&&r[a.type]?this.defaults.extensions.childTokens[a.type].forEach(o=>{let i=a[o].flat(1/0);t=t.concat(this.walkTokens(i,e))}):a.tokens&&(t=t.concat(this.walkTokens(a.tokens,e)))}}return t}use(...n){let e=this.defaults.extensions||{renderers:{},childTokens:{}};return n.forEach(t=>{let s={...t};if(s.async=this.defaults.async||s.async||!1,t.extensions&&(t.extensions.forEach(r=>{if(!r.name)throw new Error("extension name required");if("renderer"in r){let l=e.renderers[r.name];l?e.renderers[r.name]=function(...a){let o=r.renderer.apply(this,a);return o===!1&&(o=l.apply(this,a)),o}:e.renderers[r.name]=r.renderer}if("tokenizer"in r){if(!r.level||r.level!=="block"&&r.level!=="inline")throw new Error("extension level must be 'block' or 'inline'");let l=e[r.level];l?l.unshift(r.tokenizer):e[r.level]=[r.tokenizer],r.start&&(r.level==="block"?e.startBlock?e.startBlock.push(r.start):e.startBlock=[r.start]:r.level==="inline"&&(e.startInline?e.startInline.push(r.start):e.startInline=[r.start]))}"childTokens"in r&&r.childTokens&&(e.childTokens[r.name]=r.childTokens)}),s.extensions=e),t.renderer){let r=this.defaults.renderer||new F(this.defaults);for(let l in t.renderer){if(!(l in r))throw new Error(`renderer '${l}' does not exist`);if(["options","parser"].includes(l))continue;let a=l,o=t.renderer[a],i=r[a];r[a]=(...p)=>{let h=o.apply(r,p);return h===!1&&(h=i.apply(r,p)),h||""}}s.renderer=r}if(t.tokenizer){let r=this.defaults.tokenizer||new G(this.defaults);for(let l in t.tokenizer){if(!(l in r))throw new Error(`tokenizer '${l}' does not exist`);if(["options","rules","lexer"].includes(l))continue;let a=l,o=t.tokenizer[a],i=r[a];r[a]=(...p)=>{let h=o.apply(r,p);return h===!1&&(h=i.apply(r,p)),h}}s.tokenizer=r}if(t.hooks){let r=this.defaults.hooks||new Z;for(let l in t.hooks){if(!(l in r))throw new Error(`hook '${l}' does not exist`);if(["options","block"].includes(l))continue;let a=l,o=t.hooks[a],i=r[a];Z.passThroughHooks.has(l)?r[a]=p=>{if(this.defaults.async&&Z.passThroughHooksRespectAsync.has(l))return(async()=>{let g=await o.call(r,p);return i.call(r,g)})();let h=o.call(r,p);return i.call(r,h)}:r[a]=(...p)=>{if(this.defaults.async)return(async()=>{let g=await o.apply(r,p);return g===!1&&(g=await i.apply(r,p)),g})();let h=o.apply(r,p);return h===!1&&(h=i.apply(r,p)),h}}s.hooks=r}if(t.walkTokens){let r=this.defaults.walkTokens,l=t.walkTokens;s.walkTokens=function(a){let o=[];return o.push(l.call(this,a)),r&&(o=o.concat(r.call(this,a))),o}}this.defaults={...this.defaults,...s}}),this}setOptions(n){return this.defaults={...this.defaults,...n},this}lexer(n,e){return $.lex(n,e??this.defaults)}parser(n,e){return T.parse(n,e??this.defaults)}parseMarkdown(n){return(e,t)=>{let s={...t},r={...this.defaults,...s},l=this.onError(!!r.silent,!!r.async);if(this.defaults.async===!0&&s.async===!1)return l(new Error("marked(): The async option was set to true by an extension. Remove async: false from the parse options object to return a Promise."));if(typeof e>"u"||e===null)return l(new Error("marked(): input parameter is undefined or null"));if(typeof e!="string")return l(new Error("marked(): input parameter is of type "+Object.prototype.toString.call(e)+", string expected"));if(r.hooks&&(r.hooks.options=r,r.hooks.block=n),r.async)return(async()=>{let a=r.hooks?await r.hooks.preprocess(e):e,o=await(r.hooks?await r.hooks.provideLexer(n):n?$.lex:$.lexInline)(a,r),i=r.hooks?await r.hooks.processAllTokens(o):o;r.walkTokens&&await Promise.all(this.walkTokens(i,r.walkTokens));let p=await(r.hooks?await r.hooks.provideParser(n):n?T.parse:T.parseInline)(i,r);return r.hooks?await r.hooks.postprocess(p):p})().catch(l);try{r.hooks&&(e=r.hooks.preprocess(e));let a=(r.hooks?r.hooks.provideLexer(n):n?$.lex:$.lexInline)(e,r);r.hooks&&(a=r.hooks.processAllTokens(a)),r.walkTokens&&this.walkTokens(a,r.walkTokens);let o=(r.hooks?r.hooks.provideParser(n):n?T.parse:T.parseInline)(a,r);return r.hooks&&(o=r.hooks.postprocess(o)),o}catch(a){return l(a)}}}onError(n,e){return t=>{if(t.message+=`
Please report this to https://github.com/markedjs/marked.`,n){let s="<p>An error occurred:</p><pre>"+_(t.message+"",!0)+"</pre>";return e?Promise.resolve(s):s}if(e)return Promise.reject(t);throw t}}},L=new zt;function f(n,e){return L.parse(n,e)}f.options=f.setOptions=function(n){return L.setOptions(n),f.defaults=L.defaults,xe(f.defaults),f};f.getDefaults=te;f.defaults=C;f.use=function(...n){return L.use(...n),f.defaults=L.defaults,xe(f.defaults),f};f.walkTokens=function(n,e){return L.walkTokens(n,e)};f.parseInline=L.parseInline;f.Parser=T;f.parser=T.parse;f.Renderer=F;f.TextRenderer=ce;f.Lexer=$;f.lexer=$.lex;f.Tokenizer=G;f.Hooks=Z;f.parse=f;f.options;f.setOptions;f.use;f.walkTokens;f.parseInline;T.parse;$.lex;const Bt={class:"as-topbar"},Mt={class:"as-topbar-section"},Lt={class:"as-topbar-title"},Ct={key:0,class:"as-topbar-sub"},Pt={class:"as-body"},Et={class:"as-content-area"},It={key:0,class:"as-page-chip"},qt={class:"as-chip-num"},Ot={class:"as-chip-total"},Dt={class:"as-slides-track"},Zt=["innerHTML"],Qt={key:1,class:"as-dots"},Nt=["onClick","aria-label","title"],Ht={class:"as-bottombar"},jt=["disabled"],Gt={class:"as-page-label"},Ft=["disabled"],Ut={__name:"AboutSlider",props:{markdown:{type:String,required:!0},sectionTitle:{type:String,default:""},sectionSubtitle:{type:String,default:""},prevLabel:{type:String,default:"Назад"},nextLabel:{type:String,default:"Вперёд"},initialPage:{type:Number,default:0}},emits:["update:page"],setup(n,{expose:e,emit:t}){const s=n,r=t;function l(k){const u=f.lexer(k),x=[];let w="",R=[];for(const S of u)if(S.type==="heading"&&S.depth===3)R.length>0&&x.push({title:w,html:f.parser(R)}),w=S.text,R=[S];else{if(S.type==="heading"&&S.depth===2)continue;R.push(S)}if(R.length>0&&x.push({title:w,html:f.parser(R)}),x.length===0&&u.length>0){const S=u.find(q=>q.type==="heading"&&q.depth===2);x.push({title:S?S.text:"",html:f.parser(u)})}return x.filter(S=>S.html.replace(/<[^>]+>/g,"").replace(/\s+/g,"").trim().length>0)}const a=B(()=>l(s.markdown)),o=Pe(Math.max(0,s.initialPage));Ee(()=>s.markdown,()=>{o.value=0});const i=B(()=>a.value[o.value]||null);function p(k){k>=0&&k<a.value.length&&(o.value=k,r("update:page",k))}function h(){p(o.value-1)}function g(){p(o.value+1)}function c(k){k.key==="ArrowLeft"&&(k.preventDefault(),h()),k.key==="ArrowRight"&&(k.preventDefault(),g())}return e({goTo:p,current:o,pageCount:B(()=>a.value.length)}),(k,u)=>(A(),z("div",{class:"as-root",ref:"sliderRoot",tabindex:"0",onKeydown:c},[u[5]||(u[5]=m("span",{class:"debug-tag"},"AboutSlider",-1)),m("div",Bt,[u[0]||(u[0]=m("span",{class:"as-topbar-label"},"О проекте",-1)),u[1]||(u[1]=m("div",{class:"as-topbar-divider"},null,-1)),m("div",Mt,[m("span",Lt,P(n.sectionTitle),1),n.sectionSubtitle?(A(),z("span",Ct,P(n.sectionSubtitle),1)):K("",!0)])]),m("div",Pt,[u[3]||(u[3]=m("div",{class:"as-accent"},null,-1)),m("div",Et,[a.value.length>1?(A(),z("div",It,[m("span",qt,P(o.value+1),1),u[2]||(u[2]=m("span",{class:"as-chip-sep"},"/",-1)),m("span",Ot,P(a.value.length),1)])):K("",!0),m("div",Dt,[V(qe,{name:"as-fade",mode:"out-in"},{default:Ie(()=>[(A(),z("div",{key:o.value,class:"as-slide"},[m("div",{class:"as-slide-content",innerHTML:i.value.html},null,8,Zt)]))]),_:1})]),a.value.length>1?(A(),z("div",Qt,[(A(!0),z(Oe,null,De(a.value,(x,w)=>(A(),z("button",{key:w,class:Ze(["as-dot",{active:w===o.value}]),onClick:R=>p(w),"aria-label":"Страница "+(w+1),title:x.title},null,10,Nt))),128))])):K("",!0)]),u[4]||(u[4]=m("div",{class:"as-accent as-accent-right"},null,-1))]),m("div",Ht,[m("button",{class:"as-nav-arrow",disabled:o.value===0,onClick:h,"aria-label":"Назад"}," ← ",8,jt),m("span",Gt,"Страница "+P(o.value+1)+" из "+P(a.value.length),1),m("button",{class:"as-nav-arrow",disabled:o.value===a.value.length-1,onClick:g,"aria-label":"Вперёд"}," → ",8,Ft)])],544))}},Xt=be(Ut,[["__scopeId","data-v-cf2e9690"]]),Wt=`## 1. Возможности системы\r
\r
### 1.1. Каталог и поиск\r
\r
- **Каталог товаров**, представленный на четырёх вариантах:\r
- **Просмотр по сериям** – для детального просмотра карточек товара\r
  - **Быстрый подбор** – для быстрого выбора модели, не погружаясь в технические параметры\r
  - **Инженерный подбор** - **Умный поиск** по техническим параметрам (каскадные параметры, примерные аналоги) — не общий поиск от CMS.\r
- **AI-помощник подбора**\r
- **Единая строка поиска** — обработка запроса на естественном языке (вместо ручного листания каталога).\r
- **Гибкость запроса** — подбери аналог артикул ХХХ, «подбери пневмопривод к затвору ABRA ХХХ», «найди среди брендов А, B, C», «остаток, сроки поставки», «нужен сертификат».\r
- **ИИ-помощник** в каталогах: помогает выбрать оборудование, составляет фильтры, показывает карточки товара, отвечает на вопросы.\r
- **ИИ-помощник в конфигураторах:** подбирает состав сборки из каталога с приоритетом товаров с флагом «Проверено производителем».\r
\r
- **Решение проблемы составных изделий:** для оборудования с комбинациями опций количество карточек может достигать миллионов — индексация роботами невозможна, SEO-оптимизация не работает. Решение — ИИ-поиск.\r
- **Техническая документация, сертификаты, чертежи, схемы** привязаны к модели и серии, хранятся в оптимизированном для просмотра на экране (быстрый просмотр), сжатом (отправка на почту с лимитом на объем вложений), полном – для скачивания и печати. Для формирования всех вариантов используются встроенные инструменты\r
- **Информация в виде структурированной Schema для внешних ИИ-агентов** — подготовка к изменениям в недалеком будущем, когда многие перейдут на агентские закупки.\r
\r
### 1.2. Коммерческое предложение (КП)\r
\r
- **Формирование «идеального КП»**, включающего:\r
  - Коммерческую часть (цена, сроки поставки, коммерческие условия)\r
  - Техническое описание каждой единицы в составе сборки\r
  - Габаритный чертеж сборки и/или каждого изделия в составе\r
  - Электрическую схему подключения (для ЭП, БКВ, клапана, позиционера)\r
  - Пневматическую схему\r
  - Сканы всех сертификатов на каждый компонент\r
  - Технический паспорт на сборку с указанием всех компонентов и их характеристик\r
  - Руководство по эксплуатации на сборку (адаптированное) или на компоненты\r
- **Автоматическая генерация документов «на лету»** — сбор информации и документов из разных источников автоматизирован.\r
- **Хранение КП + техдокументации на диске**, выдача ссылок для скачивания клиентам.\r
- **Сертификаты, технички, паспорта** доступны для скачивания в двух форматах: оригинал от производителя и сжатый (пригодный для отправки по email).\r
- **Защита подбора** — описание для КП формируется достаточно полным и обезличенным, в виде EBOM так как КП часто включается в другое КП изготовителями арматуры.\r
\r
### 1.3. Инженерные инструменты\r
\r
- **Конфигураторы** для проектирования уникальных, сложных или составных изделий по индивидуальным техническим требованиям.\r
- **Формирование BOM/EBOM** с возможностью проставлять наценки, искать замену по параметрам, видеть сроки поставки по каждой позиции.\r
- **Автоматический или ручной запрос цены и сроков у производителей** — внутри системы или через почту.\r
- **Интерактивные конфигураторы** с правилом изоляции номенклатуры: сконфигурированное оборудование сохраняется только в личную рабочую номенклатуру пользователя и не публикуется в общем каталоге.\r
- **Таблицы соответствий** «арматура-привод» закрывают большинство стандартных запросов.\r
- **Конструктор для нестандартных условий** (например, давление питания в пневмосистеме, нестандартные схемы электроподключений).\r
\r
### 1.4. ИИ-модуль (автоматизация рутины)\r
\r
- **Распознавание ОЛ, спецификаций, текстовых запросов клиентов:** ИИ парсит неструктурированные текстовые или табличные файлы (Excel, PDF, сканы) и мгновенно формирует системный документ «Запрос клиента», являющийся структурированным описанием требований клиента к оборудованию или сборке\r
- **Интеллектуальное составление сборок:** ИИ автоматически создает сложные составные изделия, учитывая взаимную техническую сочетаемость компонентов.\r
- **Интеграция каналов связи (Email / Мессенджеры):** ИИ анализирует входящие сообщения, автоматически подбирает оборудование и формирует два связанных документа: «Запрос клиента» и «Подбор по запросу клиента».\r
- **Рабочее место с запросами:** сквозной интерфейс для ведения, ручной корректировки, согласования и конвертации запросов в КП.\r
- **Версионирование и отслеживание изменений**, протоколирование причин изменений.\r
\r
### 1.5. Интеграции\r
\r
- **Синхронизация с 1С/CRM:** двусторонняя связь личной номенклатуры, автоматический обмен ценами, персональными скидками, резервами и складскими остатками в реальном времени.\r
- **Интеграция с системой поиска тендеров** — получение номенклатуры тендерной документации для формирования Запроса клиента, автоматического составления технического предложения, формирования основы для коммерческого предложения, формирования пакета документов для подачи в тендер – файлов сертификатов, чертежей, схем, техничек и каталогов.\r
- **интеграция с Битрикс24** (лиды, контакты, сделки, КП, состав заказа/сборки).\r
\r
### 1.6. Обработка и хранение медиа\r
\r
- **Автоматический перевод чертежей и электрических схем в векторный формат** с сохранением исходного изображения — улучшает воспроизведение и позволяет использовать зашумлённые/нерезкие изображения.\r
- **Фотогалерея**, оптимизированная для быстрой загрузки, с возможностью получения оригинала.\r
- **Кадрирование и автоматическая уборка фона** — позволяет накладывать изображения на любые другие и использовать для печатных вариантов.\r
- **Возможность хранения документации и изображений на своём сервере** — в облаке или локально.\r
- **Хранение и выдача 3D и BIM-моделей** в любых форматах.\r
\r
### 1.7. Корзина и оформление заказа\r
\r
- **Сбор корзины** с товарами от разных селлеров, дилеров и производителей, включая готовые инженерные сборки.\r
- **Алгоритм разделения заказа (split):**\r
  - Готовые сборки напрямую уходят селлеру (инжиниринговой компании).\r
  - Для «россыпи» — два варианта на выбор:\r
    1. Через Агрегатора поставок (единый счёт, одна доставка)\r
    2. Прямая закупка у производителей/дилеров (заказ дробится, клиент работает с каждым поставщиком отдельно)\r
- **выбор поставщика** — после заполнения корзины клиенту предлагается отправить заявки производителю или поставщикам (выбор из списка, фильтр по регионам).\r
\r
### 1.8. AI/LLM — технологическая база\r
\r
- **Function Calling** — информация с сайта структурирована так, что любая LLM (GPT-4, Claude, Llama, Qwen) может:\r
  1. Понять запрос пользователя\r
  2. Вызвать \`search_equipment(params)\`через API системы\r
  3. Получить ответ в виде списков точного совпадения по нужным параметрам ({exact: [...]) и списка совместимого оборудования (compatible: [...]})\r
  4. Сформулировать ответ с объяснением\r
- **Масштабирование и повторное использование** — пользователи могут писать собственных агентов для автоматизации работы.\r
- **Развитие собственных моделей** на основе ответов LLM:\r
  - Обработка опросных листов и «диких» запросов технически слабых клиентов\r
  - Создание компактной специализированной модели для анализа ОЛ и составления структурированного ОЛ\r
  - Создание модели для квалификации заявки\r
  - Накопление материала для обучения более продвинутых LLM\r
  - Локальная модель продолжает работать при отсутствии доступа к коммерческим LLM\r
  - Экономия затрат на доступ к LLM\r
- **Специализированное обучение на техническом русском, жаргоне, ГОСТ** — на выходе структурированный JSON для отображения на сайтах.\r
\r
### 1.9. Модель монетизации (в процессе обсуждения)\r
\r
- **Случайные посетители:** фримиум + продажа информации (на примере auto.ru).\r
- **Производители:** взнос на поддержание, оплата дискового пространства, размещение на сайте партнёра, карточки товара, включение в ИИ-поиск, подключённый партнёр, заявка с главного сайта, покупка аналитики, адаптация сайтов, интеграция с 1С и Битрикс24.\r
- **Сайты партнёров:** оборудование от производителя — бесплатно при авторизации производителем или опции «раздача всем»; платно, если производитель не партнёр. Работа с ИИ — по количеству токенов.\r
- **Профучастники:** ежемесячный взнос (пакет пользователей), оплата за подбор (пакет/нелимитировано/поштучно), адаптация сайтов, интеграция с 1С и Битрикс24, аукцион по выполнению продажи с сайта.\r
\r
`,Kt=`## 2. Преимущества для пользователей системы\r
\r
### 2.1. Производители оборудования (и Импортёры)\r
\r
- **Самостоятельное управление техдокументацией:** определять объём и вид документации на сайте — каталоги, 3D и BIM-модели в любых форматах (для серии или для отдельной модели).\r
- **«Собственная номенклатура»** — приватные каталоги оборудования для своих сотрудников и избранных партнёров.\r
- **Оперативный ввод** новых продуктовых линеек в систему с немедленным масштабированием по всем пользователям системы без необходимости индивидуального продвижения.\r
- **Контроль РРЦ** установленные производителем на агрегаторе цены транслируются немедленно на сайты-партнеры на основе РРЦ. Цена может быть выше, но не ниже РРЦ — контролируется системой. Валютные цены обновляются централизованно. Нет демпинга и ошибок обновления.\r
- **Конфигуратор цен** с автоматическим расчётом цены на сложное оборудование (пневмоприводы, электроприводы, позиционеры, клапаны соленоидные).\r
- **AI-помощник** для подбора сложного оборудования.\r
- **Кастомные AI-обработчики запросов клиентов** — использование собственных нейросетей, выдающих ответ на собственных сайтах или сайтах – партнерах с учетом особенностей оборудования Производителя.\r
- **Единая библиотека технической информации** — всегда актуальна, выкладка непосредственно от производителя конечному потребителю.\r
- **Единые цены** на всех сайтах \r
- **Получение аналитики:** количество запросов с сайтов дистрибьюторов, товарные группы, географический интерес конечных потребителей.\r
- **Анализ плюсов и минусов своей продукции** в сравнении с конкурентами и ценами конкурентов.\r
\r
### 2.2. Инжиниринговые компании (технические эксперты платформы)\r
\r
- **Создание сложных технических сборок** (запорная арматура + электропривод + датчики + крепёж) и продажа комплекта как единого изделия под собственной карточкой товара.\r
- **Формирование BOM/EBOM** с наценками, поиском замены по параметрам, сроками поставки по каждой позиции.\r
- **Автоматический или ручной запрос цены и сроков у производителей** — внутри системы или через почту.\r
- **Быстрый подбор для тендеров.**\r
- **Формирование идеального КП.**\r
- **Интеграция с системой поиска тендеров** — получение номенклатуры.\r
- **Установка скидок и наценок** к базовым РРЦ для выбранных клиентов — автоматическое формирование КП.\r
- **Ограничение отображаемых разделов каталогов** для сотрудников по брендам/сериям, расстановка приоритетов для подбора.\r
- **Приватные каталоги** — не на сайте, но доступны сотрудникам и участвуют в подборах.\r
- **Приватный список номенклатуры** с синхронизацией с 1С и номенклатурой сайта.\r
- **Формирование BOM/EBOM КП без указания артикула производителя.**\r
- **Кастомные паспорта товара** под собственными артикулами, кастомные каталоги, кастомные технические документы.\r
- **Кастомные электрические схемы подключения и габаритные чертежи.**\r
- **ИИ-аудит сборок** на корректность кодировок и сочетаемость компонентов.\r
- **Распознавание спецификаций** (Excel, PDF, сканы) и автоматическое формирование «Запроса клиента».\r
- **Интеграция email/мессенджеров** — ИИ подбирает оборудование из каталога по входящим сообщениям.\r
- **Рабочее место с запросами** — ведение, корректировка, согласование, конвертация в КП.\r
- **Синхронизация с 1С/CRM** — цены, скидки, резервы, остатки в реальном времени.\r
- **Проектирование нестандартных МК, скоб, адаптаций** — библиотека и автоматизация.\r
- **Комплектация и MBOM** — поиск аналогов по наличию, ценам, срокам.\r
\r
### 2.3. Дилеры производителей и Селлеры\r
\r
- **Размещение карточек товаров** со своими ценами и остатками на Маркете.\r
- **Получение заказов с Сайта-агрегатора.**\r
- **Быстрая и легкая** комплектация комплексного заказа через агрегатор.\r
- **Возможность создать для клиента идеальное КП.**\r
- **Доступ к ИИ-модулю** для автоматизации обработки входящих заявок.\r
- **Установка скидок и наценок** для выбранных клиентов.\r
- **Синхронизация каталогов** с номенклатурой в 1С/CRM.\r
- **Расстановка приоритетов подбора** — преимущество собственной продукции в выдаче.\r
\r
### 2.4. Сайты-партнёры (дистрибьюторы)\r
\r
- **Выкладка полноценного каталога** с инженерными фильтрами на собственный сайт без усилий — быстрое развёртывание (минуты, а не дни/месяцы).\r
- **Установка наценки** к базовым РРЦ производителей для своего сайта.\r
- **Автоматический пересчёт валютных цен** в рубли или другую валюту, выбор валюты отображения.\r
- **Выкладка по видам оборудования** — одно мини-приложение = один раздел на сайте.\r
- **Выбор брендов и серий** из списка доступных на тарифе (бесплатные, платные, требующие разрешения производителя).\r
- **Отсутствие необходимости** поддерживать базу по товарам и ценам в актуальном виде.\r
- **Профессиональный поиск по параметрам**, а не общий от CMS.\r
- **Входящие заказы** обрабатываются по внутренним правилам локальной CMS.\r
- **Сбор локальных заявок** на своём сайте.\r
\r
### 2.5. Конечные потребители (B2B-покупатели)\r
\r
- **Неавторизованный пользователь:**\r
  - Свободный просмотр каталогов, фильтры, карточки товаров (базовые позиции и готовые сборки).\r
  - Сбор корзины с товарами от разных селлеров и производителей.\r
  - Выбор схемы закупки: через Агрегатора (единый счёт) или напрямую у дилеров.\r
- **Авторизованный пользователь (профессиональный B2B-клиент):**\r
  - Полный доступ к публичным каталогам, ценам, складским остаткам.\r
  - Интерактивные конфигураторы для проектирования сложных изделий.\r
  - ИИ-модуль (аудит сборок, распознавание спецификаций, интеграция каналов связи).\r
  - Синхронизация с 1С/CRM.\r
- **Настраиваемые системные виджеты** (курсы валют, справочник химстойкости, расшифровка ЕТТ, документы из медиабиблиотеки), добавление кастомных виджетов (Markdown, PDF, изображения).\r
- **Получение полной технической информации** об арматуре и устройствах управления.\r
- **Поиск и подбор по техническим характеристикам**, адаптированный как для профессионалов, так и для людей без специального образования.\r
- **самостоятельный выбор готовых решений** — конечный потребитель может выбрать готовую сборку без помощи инженера.\r
\r
### 2.6. Поставщик-консолидатор (Агрегатор поставок)\r
\r
- **Роль «одного окна»** для конечного покупателя:\r
  - Консолидация под заявку клиента оборудования от множества разных производителей и селлеров.\r
  - Получение единой оплаты.\r
  - Проверка инженерной совместимости оборудования.\r
  - Контроль качества, переупаковка.\r
  - Отгрузка всего заказа одной партией (один пакет документов) в адрес клиента.\r
- **взятие на себя валютных рисков, разных сроков поставки**, складского и логистического хозяйства.\r
\r
### 2.7. Тендерные отделы и снабженцы\r
- **Автоматическое получение тендерной документации** из партнерской системы парсинга тендеров в компактном и читаемом виде, пригодном для передачи в подбор оборудования.\r
- **Обработка тендерной документации** — ИИ анализирует тендер, формирует EBOM.\r
- **Быстрый подбор для тендеров** — поиск по номенклатуре тендера, автоматическое сопоставление с каталогом.\r
- **Аукцион/биржа EBOM** — раздел «Получить решение»: заказчик вводит требования, ИИ создаёт EBOM и выставляет на биржу для выполнения селлерами.\r
\r
`,Vt=`## 3. Преимущества по типам потребителей\r
\r
### 3.1. Производители\r
\r
| Преимущество | Суть |\r
|---|---|\r
| **Экономия на продвижении** | Не нужно индивидуально продвигать новые линейки — они сразу доступны на агрегаторе и сайтах партнёров. |\r
| **Защита цен** | Единые РРЦ на всех сайтах, нет демпинга, ошибок обновления валютных цен. |\r
| **Контроль информации** | Производитель сам управляет объёмом и видом документации; информация всегда актуальна. |\r
| **Прямой выход на конечника** | Выкладка фото, каталогов, моделей напрямую конечному потребителю без посредников. |\r
| **Аналитика** | Данные о географии и товарных группах интереса, сравнение с конкурентами. |\r
| **Агентский подход** | Переход от модели push-продаж к контекстно-ориентированному «живому сайту». |\r
| **снижение затрат на техдокументацию** | Система сама обрабатывает изображения, переводит чертежи в вектор, генерирует документы. |\r
\r
### 3.2. Инжиниринговые компании\r
\r
| Преимущество | Суть |\r
|---|---|\r
| **Скорость подготовки КП** | Сборка пакета документов (КП, чертежи, схемы, сертификаты, паспорт) автоматизирована. |\r
| **Автоматизация рутины** | ИИ разбирает почту, мессенджеры, сканы ОЛ, формирует запросы и подборы. |\r
| **Защита подбора** | Обезличенное описание в КП; сконфигурированные изделия хранятся в приватной номенклатуре. |\r
| **Гибкая коммерческая модель** | Наценки и скидки под конкретных клиентов, скрытие брендов конкурентов. |\r
| **Единое рабочее место** | Сквозной интерфейс: запрос → подбор → версионирование → КП. |\r
| **Снижение ошибок** | ИИ аудирует кодировки и сочетаемость компонентов. |\r
| **быстрое реагирование на тендеры** | Интеграция с поиском тендеров и автоматический подбор номенклатуры. |\r
\r
### 3.3. Дилеры / Селлеры\r
\r
| Преимущество | Суть |\r
|---|---|\r
| **Готовый канал продаж** | Заказы приходят с Сайта-агрегатора. |\r
| **Идеальное КП** | Вся техдокументация генерируется автоматически. |\r
| **Синхронизация с учётными системами** | Цены, остатки, номенклатура — в реальном времени через 1С/CRM. |\r
| **Конкурентное преимущество** | ИИ-подбор и приоритизация собственной продукции в выдаче. |\r
| **минимальные затраты на интеграцию** | Быстрое развёртывание на готовом сайте или с нуля. |\r
\r
### 3.4. Сайты-партнёры (дистрибьюторы)\r
\r
| Преимущество | Суть |\r
|---|---|\r
| **Быстрый запуск** | Каталог с инженерными фильтрами разворачивается за минуты. |\r
| **Нулевые затраты на наполнение** | Не нужно собирать техдокументацию, обновлять цены и остатки. |\r
| **Профессиональный поиск** | Специализированный параметрический поиск, а не общий от CMS. |\r
| **Гибкие тарифы** | Бесплатные/платные бренды, выбор под свой рынок. |\r
| **Собственная коммерческая политика** | Наценки к РРЦ, своя валюта отображения. |\r
| **сбор локальных заявок** | Заявки обрабатываются по внутренним правилам CMS партнёра. |\r
\r
### 3.5. Конечные потребители\r
\r
| Преимущество | Суть |\r
|---|---|\r
| **Единый источник информации** | Не нужно обходить сайты всех производителей — вся информация в одном месте. |\r
| **Доступный поиск** | Система адаптирована и для инженеров, и для людей без специального образования. |\r
| **Простота выбора** | Привычный интерфейс маркетплейса: поиск → фильтры → корзина → заказ. |\r
| **Готовые решения** | Можно купить готовую инженерную сборку, не вникая в технические детали. |\r
| **Свобода выбора поставщика** | Варианты: единый счёт через агрегатора или прямые закупки у дилеров. |\r
| **Прозрачность** | Видны цены, сроки, рейтинги; нет скрытых преференций. |\r
| **снижение риска ошибки** | ИИ проверяет совместимость компонентов ещё на этапе подбора. |\r
\r
### 3.6. Поставщик-консолидатор\r
\r
| Преимущество | Суть |\r
|---|---|\r
| **Роль «одного окна»** | Консолидация, проверка совместимости, единая отгрузка. |\r
| **Добавленная стоимость** | Клиент платит за сервис комплектации и логистики. |\r
| **Снижение рисков клиента** | Валютные риски и риски сроков берёт на себя консолидатор. |\r
| **независимость от производителей** | Консолидатор работает со всеми, не привязан к одному бренду. |\r
\r
### 3.7. Тендерные отделы и снабженцы\r
\r
| Преимущество | Суть |\r
|---|---|\r
| **Скорость** | Автоматический разбор тендерной документации, формирование EBOM за минуты. |\r
| **Точность** | Сопоставление требований тендера с фактическим каталогом, исключение ошибок ручного подбора. |\r
| **Биржа EBOM** | Возможность выставить EBOM на аукцион и получить лучшие условия от селлеров. |\r
\r
`,Jt=`## Архитектура системы и основные понятия\r
\r
### Архитектура\r
\r
Проект представляет собой экосистему из трёх ключевых ИТ-продуктов:\r
\r
- **Структурированное хранилище технической информации** — единая база данных по арматуре и устройствам управления\r
- **Сайт-Агрегатор** — каталоги и конфигураторы оборудования, система формирования КП, спецификаций, паспортов и технической информации, система оформления заказов на покупку\r
- **Сеть Сайтов-партнёров** — внешние витрины клиентов, интегрированные через мини-приложения\r
\r
### Ролевая модель участников\r
\r
Для описания цепочки поставок, ценообразования и обработки заказов на платформе используются следующие роли:\r
\r
- **Производитель (Импортёр)** — завод или официальный импортёр промышленного оборудования. Продаёт продукцию под уникальными брендами и кодировками (артикулами). Напрямую розничные или мелкооптовые заказы не обрабатывает, а реализует товары исключительно через свою дилерскую сеть.\r
- **Дилер Производителя** — официальная торговая организация, авторизованная Производителем. Дилер размещает карточки товаров со своими ценами и остатками и напрямую отвечает за поставку.\r
- **Инжиниринговая компания** — технический эксперт платформы. Создаёт сложные технические сборки (например, запорная арматура + электропривод + датчики + крепёж) и продаёт такой комплект как единое изделие под собственной карточкой товара.\r
- **Селлер** — обобщённое понятие для любого продавца, имеющего свои карточки товаров. Роль Селлера может выполнять как Дилер, так и Инжиниринговая компания.\r
- **Поставщик-консолидатор** — сервисно-логистическая организация, выступающая главным «одним окном» для конечного покупателя. Консолидирует под заявку клиента оборудование от множества разных Производителей и Селлеров. Его функции: получение единой оплаты, проверка инженерной совместимости оборудования, контроль качества, переупаковка и отгрузка всего заказа одной партией (одним пакетом документов) в адрес Клиента.\r
- **Сайт-партнёр** — внешний сайт (например, крупного интегратора или регионального дилера), на котором развёрнуты мини-приложения (виджеты) каталога. Карточки товаров синхронизируются с CMS Сайта-партнёра, а входящие заказы обрабатываются по внутренним правилам этой локальной CMS.\r
\r
### Основные понятия (BOM)\r
\r
- **EBOM (Engineering BOM)** — инженерная спецификация. Конструкторская спецификация, описывающая общие характеристики оборудования без привязки к конкретному производителю. Пример: «Клапан соленоидный 5/2 взрывозащищённый Ex ia, резьба портов ¼" — 4 шт.» — без указания артикула.\r
- **MBOM (Manufacturing BOM)** — производственная спецификация поставки или закупки. Разворачивает EBOM до конкретных артикулов производителей: модель, бренд, код заказа.\r
`,Yt={class:"about-section-page"},en={__name:"AboutSection",setup(n){const e=Me(),t=Le(),s=B(()=>({"about-capabilities":"capabilities","about-benefits-users":"benefits-users","about-benefits-types":"benefits-types","about-architecture":"architecture"})[e.name]||""),r={capabilities:{title:"Возможности системы",subtitle:"Каталог, поиск, инженерные инструменты, ИИ-модуль, интеграции и многое другое",md:Wt},"benefits-users":{title:"Преимущества для пользователей системы",subtitle:"Что получает каждый тип участника: производители, инжиниринговые компании, дилеры, партнёры, потребители",md:Kt},"benefits-types":{title:"Преимущества по типам потребителей",subtitle:"Сводная таблица: какое преимущество даёт система для каждого типа потребителя",md:Vt},architecture:{title:"Архитектура системы и основные понятия",subtitle:"ИТ-продукты, ролевая модель участников, терминология BOM",md:Jt}},l=B(()=>r[s.value]||{title:"",subtitle:"",md:""}),a=B(()=>l.value.md),o=B(()=>{const g=parseInt(e.query.page);return g>0?g-1:0}),i=B(()=>[{name:"Главная",to:"/"},{name:"О проекте",to:"/about"},{name:l.value.title,to:e.path}]);function p(g){g.to&&t.push(g.to)}function h(g){const c={...e.query};g===0?delete c.page:c.page=String(g+1),t.replace({query:c})}return(g,c)=>(A(),z("div",Yt,[c[0]||(c[0]=m("span",{class:"debug-tag"},"AboutSection",-1)),V(Ce,{items:i.value,onNavigate:p},null,8,["items"]),V(Xt,{markdown:a.value,sectionTitle:l.value.title,sectionSubtitle:l.value.subtitle,initialPage:o.value,"onUpdate:page":h},null,8,["markdown","sectionTitle","sectionSubtitle","initialPage"])]))}},an=be(en,[["__scopeId","data-v-634fa918"]]);export{an as default};
