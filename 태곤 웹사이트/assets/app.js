
const KRW = (n)=> new Intl.NumberFormat('ko-KR').format(n);
const CART_KEY = 'singsing_cart';

// --- normalize helpers (robust for old saved carts / emoji labels) ---
const _stripEmoji = (s)=> (s||'').toString().trim().replace(/^[^A-Za-z0-9_ㄱ-ㅎ가-힣]+/,'').trim();

const normalizeProductId = (productId, name='')=>{
  const raw = _stripEmoji(productId);
  // already an id?
  const known = ['carrot_soil','carrot_mid','carrot_top','potato_special','kohlrabi','onion_mid','cabbage_38','sweetpotato_mid'];
  if(known.includes(raw)) return raw;

  const label = _stripEmoji(name || productId);

  if(label.includes('국내산 흙당근')) return 'carrot_soil';
  if(label.includes('제주당근(중)')) return 'carrot_mid';
  if(label.includes('제주당근(상)')) return 'carrot_top';
  if(label.includes('제주감자(특)')) return 'potato_special';
  if(label.includes('콜라비')) return 'kohlrabi';
  if(label.includes('양파')) return 'onion_mid';
  if(label.includes('양배추')) return 'cabbage_38';
  if(label.includes('꿀고구마')) return 'sweetpotato_mid';

  return raw || label;
};

const normalizePack = (pack, productId)=>{
  let p = parseInt((pack||'').toString().replace(/kg/gi,''), 10);
  if(!Number.isFinite(p) || p<=0){
    p = (productId==='cabbage_38') ? 2 : 1;
  }
  // enforce allowed packs
  if(productId==='cabbage_38'){
    if(!(p===2 || p===4)) p = 2;
  } else {
    if(!([1,2,3,5].includes(p))) p = 1;
  }
  return p;
};

const normalizeQty = (qty)=>{
  const q = parseInt((qty??1).toString().replace(/[^0-9]/g,''), 10);
  if(!Number.isFinite(q) || q<1) return 1;
  return q;
};

const normalizeItem = (it)=>{
  const item = Object.assign({}, it||{});
  item.name = (item.name||'').toString();
  item.productId = normalizeProductId(item.productId, item.name);
  item.pack = normalizePack(item.pack, item.productId);
  item.qty  = normalizeQty(item.qty);
  return item;
};

const getCart = ()=>{
  let cart = [];
  try{
    cart = JSON.parse(localStorage.getItem(CART_KEY) || '[]') || [];
  }catch(e){
    cart = [];
  }
  const norm = cart.map(normalizeItem);
  // 저장 포맷이 꼬여있으면 정리해서 다시 저장
  try{
    const a = JSON.stringify(cart);
    const b = JSON.stringify(norm);
    if(a !== b){
      localStorage.setItem(CART_KEY, b);
    }
  }catch(e){}
  return norm;
};

const setCart = (cart)=>{
  const norm = (cart||[]).map(normalizeItem);
  localStorage.setItem(CART_KEY, JSON.stringify(norm));
};

const addToCart = (item)=>{
  const cart = getCart();
  const it = normalizeItem(item);
  const key = `${it.productId}:${it.pack}`;
  const found = cart.find(x=>`${x.productId}:${x.pack}`===key);
  if(found){ found.qty = normalizeQty(found.qty + it.qty); }
  else{ cart.push(it); }
  setCart(cart);
  toast(it.toastMsg || '장바구니에 담겼습니다 ✅');
  updateCartCount();
};

const removeFromCart = (productId, pack)=>{
  const pid = normalizeProductId(productId, productId);
  const pk  = normalizePack(pack, pid);
  const cart = getCart().filter(x=>!(x.productId===pid && x.pack===pk));
  setCart(cart);
  updateCartCount();
};

const updateQty = (productId, pack, qty)=>{
  const pid = normalizeProductId(productId, productId);
  const pk  = normalizePack(pack, pid);
  const cart = getCart();
  const item = cart.find(x=>x.productId===pid && x.pack===pk);
  if(item){ item.qty = normalizeQty(qty); }
  setCart(cart);
  updateCartCount();
};

const cartCount = ()=> getCart().reduce((a,b)=> a + normalizeQty(b.qty), 0);

const updateCartCount = ()=>{
  const el = document.querySelector('[data-cart-count]');
  if(el) el.textContent = cartCount();
};

const isBeforeNine = ()=>{
  const now = new Date();
  const hour = now.getHours();
  const min = now.getMinutes();
  return (hour < 9) || (hour===9 && min===0);
};

const shipText = ()=> isBeforeNine() ? '오늘 출고 가능(정산완료 기준)' : '익일 출고(정산완료 기준)';
const toast = (msg)=>{
  const t = document.createElement('div');
  t.textContent = msg;
  t.style.position='fixed';
  t.style.left='50%';
  t.style.bottom='24px';
  t.style.transform='translateX(-50%)';
  t.style.background='#111827';
  t.style.color='#fff';
  t.style.padding='12px 14px';
  t.style.borderRadius='14px';
  t.style.fontWeight='900';
  t.style.zIndex='10000';
  t.style.boxShadow='0 18px 35px rgba(0,0,0,.25)';
  document.body.appendChild(t);
  setTimeout(()=>{ t.remove(); }, 1800);
};

document.addEventListener('DOMContentLoaded', ()=> updateCartCount());
