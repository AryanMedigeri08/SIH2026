export function speechTokens(text='') {
  let index=0;
  return [...text.matchAll(/\s+|\S+/gu)].map(match=>({text:match[0],start:match.index,
    wordIndex:/\s/u.test(match[0][0])?-1:index++}));
}

export function wordAtBoundary(text,charIndex) {
  const words=speechTokens(text).filter(token=>token.wordIndex>=0);
  return words.find(token=>charIndex>=token.start&&charIndex<token.start+token.text.length)?.wordIndex
    ?? words.filter(token=>token.start<=charIndex).at(-1)?.wordIndex ?? -1;
}

// Provider TTS currently returns audio without alignment timestamps. Drive its
// visual word cue from actual playback time; native speech uses word boundaries.
export function wordAtPlayback(text,seconds,duration) {
  if(!Number.isFinite(duration)||duration<=0)return -1;
  const words=speechTokens(text).filter(token=>token.wordIndex>=0);
  const weights=words.map(token=>Math.max(2,[...token.text].length)+(/[.!?।,;:]$/u.test(token.text)?3:0));
  const target=Math.max(0,Math.min(1,seconds/duration))*weights.reduce((sum,value)=>sum+value,0);
  let elapsed=0;
  for(let index=0;index<words.length;index++){elapsed+=weights[index];if(target<elapsed)return index;}
  return words.at(-1)?.wordIndex??-1;
}
