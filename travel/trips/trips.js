// ============ TRIPS REGISTRY ============
// travel/ 配下の「旅程ページ」の一覧。新しい旅を作ったらここに1件追加する。
// - slug   : travel/trips/<slug>/index.html のフォルダ名
// - start/end : YYYY-MM-DD（end を過ぎると自動で Past に移動）
// - route  : 経路の1行表示
// - status : 'planning' | 'booked' | 'done'（表示用ラベル）
window.TRIPS = [
  {
    slug: '2026-10-nepal',
    title: 'Nepal 2026',
    subtitle: 'Everest View Trek + Pokhara / Kathmandu / Guangzhou',
    start: '2026-10-24',
    end: '2026-11-03',
    route: 'Tokyo → Pokhara → Kathmandu → Everest Region → Guangzhou → Tokyo',
    countries: ['🇳🇵', '🇨🇳'],
    status: 'planning',
    members: 4
  }
];
