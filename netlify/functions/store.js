/*
  netlify/functions/store.js

  Serverless function used as the production backend when hosting on Netlify.
  Purpose: provide the same REST-like API surface used by `store.py` so the
  static site can operate without running a Python backend in the hosting
  environment.

  Recent fixes (this commit):
  - Normalizes `route` to remove duplicated slashes (prevents paths like
    "//api/products" from being created on some requests).
  - Fixes a product-listing route check that previously matched "//api/products".

  Notes: This file intentionally mirrors `store.py` behavior (auth tokens,
  product catalog, shipping/coupons, PIX simulation) so the front-end can use
  `/.netlify/functions/store` as the API base path.
*/
const crypto = require("crypto");

const products = [
  { id: 1, name: "Fone Bluetooth TWS Pro", description: "Som hi-fi, cancelamento de ruído ativo, 30h de bateria com estojo carregador.", price: 79.9, original_price: 199.9, category: "Eletrônicos", emoji: "🎧", sold: 1247, rating: 4.7, reviews: 312, stock: 45, tags: ["frete gratis", "mais vendido"] },
  { id: 2, name: "Smartwatch Fitness Tracker", description: "Monitor cardíaco, GPS integrado, resistente à água IP68, 14 dias de bateria.", price: 129.9, original_price: 299.9, category: "Eletrônicos", emoji: "⌚", sold: 893, rating: 4.5, reviews: 201, stock: 28, tags: ["frete gratis"] },
  { id: 3, name: "Ring Light LED 26cm", description: "3 temperaturas de cor, tripé ajustável incluso, ideal para lives e selfies.", price: 49.9, original_price: 119.9, category: "Eletrônicos", emoji: "💡", sold: 2105, rating: 4.3, reviews: 578, stock: 120, tags: ["mais vendido"] },
  { id: 4, name: "Mochila Anti-Furto USB", description: "Porta USB externa, compartimento laptop 15.6, material impermeável.", price: 89.9, original_price: 189.9, category: "Acessórios", emoji: "🎒", sold: 674, rating: 4.6, reviews: 189, stock: 63, tags: ["frete gratis"] },
  { id: 5, name: "Garrafa Térmica 500ml LED", description: "Aço inox 304, mantém temperatura por 12h, display LED de temperatura.", price: 59.9, original_price: 139.9, category: "Casa", emoji: "🧴", sold: 1562, rating: 4.8, reviews: 445, stock: 95, tags: ["mais vendido"] },
  { id: 6, name: "Mini Projetor Portátil 1080p", description: "Full HD nativo, WiFi e Bluetooth, compatível com celular e notebook.", price: 299.9, original_price: 599.9, category: "Eletrônicos", emoji: "📽️", sold: 431, rating: 4.4, reviews: 98, stock: 15, tags: ["frete gratis"] },
  { id: 7, name: "Organizador Maquiagem LED 360", description: "Espelho com LED, rotação 360, compartimentos ajustáveis, acrílico premium.", price: 69.9, original_price: 159.9, category: "Beleza", emoji: "💄", sold: 987, rating: 4.6, reviews: 267, stock: 54, tags: [] },
  { id: 8, name: "Luminária Lunar 3D 15cm", description: "Recarregável USB, 16 cores com controle, toque para trocar cor.", price: 39.9, original_price: 99.9, category: "Casa", emoji: "🌙", sold: 1834, rating: 4.9, reviews: 623, stock: 200, tags: ["mais vendido"] },
  { id: 9, name: "Câmera Segurança WiFi 360", description: "1080p, visão noturna colorida, áudio bidirecional, detecção de movimento.", price: 89.9, original_price: 219.9, category: "Eletrônicos", emoji: "📷", sold: 1120, rating: 4.3, reviews: 334, stock: 72, tags: ["frete gratis"] },
  { id: 10, name: "Kit Skincare Coreano 5 passos", description: "Limpeza, tônico, sérum vitamina C, hidratante ácido hialurônico, protetor solar.", price: 119.9, original_price: 279.9, category: "Beleza", emoji: "✨", sold: 756, rating: 4.7, reviews: 198, stock: 38, tags: ["frete gratis"] },
  { id: 11, name: "Umidificador Ultrassônico 300ml", description: "Ultra silencioso, LED decorativo 7 cores, desligamento automático.", price: 54.9, original_price: 129.9, category: "Casa", emoji: "💨", sold: 1345, rating: 4.5, reviews: 401, stock: 88, tags: [] },
  { id: 12, name: "Óculos de Sol Polarizado UV400", description: "Lentes polarizadas, proteção UV400, design unissex, estojo rígido incluso.", price: 44.9, original_price: 109.9, category: "Acessórios", emoji: "🕶️", sold: 2011, rating: 4.4, reviews: 567, stock: 150, tags: ["mais vendido"] },
  { id: 13, name: "Caixa de Som Bluetooth 20W", description: "Som estéreo, à prova d'água IPX7, 12h de bateria, luzes LED.", price: 99.9, original_price: 229.9, category: "Eletrônicos", emoji: "🔊", sold: 923, rating: 4.6, reviews: 276, stock: 56, tags: ["frete gratis"] },
  { id: 14, name: "Carregador Portátil 20000mAh", description: "Carga rápida 22.5W, 3 saídas USB, display LED, compatível com todos.", price: 69.9, original_price: 159.9, category: "Eletrônicos", emoji: "🔋", sold: 1678, rating: 4.5, reviews: 489, stock: 110, tags: ["mais vendido"] },
  { id: 15, name: "Difusor de Aromas 500ml", description: "Ultrassônico, 4 modos de timer, LED ambiente, cobre até 40m².", price: 79.9, original_price: 179.9, category: "Casa", emoji: "🌿", sold: 534, rating: 4.7, reviews: 116, stock: 76, tags: [] },
  { id: 16, name: "Pano de Microfibra Profissional", description: "Superabsorvente, sem fiapos, pacote com 6 unidades de varias cores.", price: 24.9, original_price: 69.9, category: "Casa", emoji: "🧽", sold: 1422, rating: 4.6, reviews: 298, stock: 94, tags: [] },
  { id: 17, name: "Cafeteira Elétrica Compacta 600W", description: "Aroma intenso, bico antiderramamento, tanque 1.2L, filtro permanente.", price: 129.9, original_price: 289.9, category: "Casa", emoji: "☕", sold: 389, rating: 4.4, reviews: 83, stock: 62, tags: [] },
  { id: 18, name: "Fone Gamer 7.1 Surround", description: "Iluminação RGB, microfone retrátil, encaixe macio, som imersivo.", price: 149.9, original_price: 329.9, category: "Eletrônicos", emoji: "🎧", sold: 677, rating: 4.5, reviews: 201, stock: 34, tags: ["frete gratis"] },
  { id: 19, name: "Conjunto de Panelas 5 peças", description: "Revestimento antiaderente, cabos embaçados, lavagem fácil.", price: 219.9, original_price: 499.9, category: "Casa", emoji: "🍳", sold: 289, rating: 4.6, reviews: 113, stock: 42, tags: ["mais vendido"] },
  { id: 20, name: "Mochila de Viagem 40L", description: "Resistente, bolsos laterais, compartimento para notebook, cadeado incluso.", price: 129.9, original_price: 259.9, category: "Acessórios", emoji: "🎒", sold: 532, rating: 4.7, reviews: 181, stock: 73, tags: ["frete gratis"] },
  { id: 21, name: "Squeeze Térmico 750ml", description: "Botão press, tampa anti-vazamento, corpo inox, cor fosca.", price: 39.9, original_price: 89.9, category: "Esporte", emoji: "🥤", sold: 830, rating: 4.5, reviews: 150, stock: 118, tags: [] },
  { id: 22, name: "Lâmpada LED Smart RGB", description: "Controlada por app, 16 milhões de cores, temporizador inteligente.", price: 49.9, original_price: 129.9, category: "Casa", emoji: "💡", sold: 420, rating: 4.6, reviews: 214, stock: 78, tags: [] },
  { id: 23, name: "Aspirador de Pó Robô Inteligente", description: "Mapeamento laser, app WiFi, 120min autonomia, aspira e passa pano.", price: 399.9, original_price: 899.9, category: "Casa", emoji: "🤖", sold: 234, rating: 4.3, reviews: 67, stock: 12, tags: ["frete gratis"] },
  { id: 24, name: "Perfume Importado 100ml EDT", description: "Fragrância amadeirada, longa duração 8h+, frasco premium.", price: 89.9, original_price: 229.9, category: "Beleza", emoji: "🧴", sold: 612, rating: 4.7, reviews: 178, stock: 41, tags: ["frete gratis"] },
  { id: 25, name: "Teclado Mecânico 60% RGB", description: "Switch blue, retroiluminação RGB, hot-swap, USB-C, compacto.", price: 149.9, original_price: 329.9, category: "Eletrônicos", emoji: "⌨️", sold: 556, rating: 4.8, reviews: 189, stock: 34, tags: ["frete gratis"] },
  { id: 26, name: "Tapete de Yoga Antiderrapante", description: "TPE ecológico, 6mm espessura, 183x61cm, alça transporte inclusa.", price: 44.9, original_price: 109.9, category: "Saúde", emoji: "🧘", sold: 445, rating: 4.5, reviews: 112, stock: 89, tags: [] },
  { id: 27, name: "Mouse Gamer 7200 DPI", description: "Sensor óptico, 6 botões programáveis, RGB, 12000 cliques.", price: 59.9, original_price: 149.9, category: "Eletrônicos", emoji: "🖱️", sold: 1123, rating: 4.4, reviews: 345, stock: 96, tags: [] },
  { id: 28, name: "Organizador de Cabos Magnético", description: "Silicone premium, 6 slots, base adesiva, compatível com todos cabos.", price: 19.9, original_price: 49.9, category: "Acessórios", emoji: "🧲", sold: 3201, rating: 4.3, reviews: 890, stock: 500, tags: ["mais vendido"] }
];

const coupons = {
  NOVA10: { discount: 10, type: "percent", min_value: 50, label: "10% OFF" },
  NOVA20: { discount: 20, type: "percent", min_value: 100, label: "20% OFF" },
  FRETE5: { discount: 5, type: "fixed", min_value: 30, label: "R$ 5OFF" },
  PRIMEIRACOMPRA: { discount: 15, type: "percent", min_value: 80, label: "15% OFF primeira compra" },
};

const shippingTable = [
  [1, 19999, "SP", 12.9, 3],
  [20000, 23999, "RJ", 14.9, 5],
  [30000, 39999, "MG", 16.9, 6],
  [40000, 48999, "BA", 18.9, 8],
  [50000, 57999, "PE", 19.9, 9],
  [60000, 63999, "CE", 21.9, 10],
  [70000, 73999, "DF", 15.9, 5],
  [80000, 88999, "PR", 17.9, 7],
  [90000, 99999, "RS", 19.9, 8],
  [0, 99999, "OUTROS", 22.9, 10],
];

const quizQuestions = [
  { id: 1, prompt: "Qual dos seguintes é um tipo de dado primitivo em Python?", options: ["Lista", "Dicionário", "Inteiro", "Classe"], correct_index: 2, explanation: "O tipo inteiro (int) é um tipo primitivo em Python. Listas e dicionários são tipos de coleção, e classes são estruturas de definição de objetos." },
  { id: 2, prompt: "O que significa HTML em desenvolvimento web?", options: ["HyperText Markup Language", "HighText Markdown Language", "Hyperlink Media Language", "HyperText Making Language"], correct_index: 0, explanation: "HTML significa HyperText Markup Language e é a linguagem de marcação usada para estruturar páginas web." },
  { id: 3, prompt: "Qual atributo HTML usamos para carregar um arquivo CSS externo?", options: ["src", "href", "link", "rel"], correct_index: 1, explanation: "O atributo href é usado dentro da tag <link> para referenciar um arquivo CSS externo." },
  { id: 4, prompt: "Qual comando Git cria um novo branch local?", options: ["git branch nome", "git checkout main", "git clone nome", "git push origin"], correct_index: 0, explanation: "O comando git branch nome cria um novo branch local com o nome especificado." },
];

const learningTips = [
  "Quebre problemas grandes em etapas menores antes de codificar.",
  "Comente seu código com clareza para lembrar por que cada parte existe.",
  "Use o console do navegador para inspecionar variáveis em JavaScript rapidamente.",
  "Pratique algoritmos pequenos diariamente para fortalecer lógica de programação.",
  "Sempre teste seu código com casos extremos para evitar bugs inesperados.",
];

const users = [];
const sessions = [];
const orders = [];
let nextUserId = 1;
let nextOrderId = 1;

const respond = (status, data) => ({
  statusCode: status,
  headers: {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  },
  body: JSON.stringify(data),
});

const hashPassword = (password) =>
  crypto.createHash("sha256").update(password, "utf8").digest("hex");

const generateToken = () => crypto.randomBytes(24).toString("hex");

const generatePixCode = () => {
  const random = crypto.randomBytes(12).toString("hex").toUpperCase();
  return `PIX${random}`;
};

const calcShipping = (zipCode) => {
  let cepNum = 0;
  try {
    cepNum = parseInt((zipCode || "").replace(/[^0-9]/g, ""), 10);
  } catch (e) {
    return { price: 22.9, days: 10, state: "OUTROS" };
  }
  for (const [start, end, state, price, days] of shippingTable) {
    if (cepNum >= start && cepNum <= end) {
      return { price, days, state };
    }
  }
  return { price: 22.9, days: 10, state: "OUTROS" };
};

const getCategories = () => [...new Set(products.map((p) => p.category))].sort();

const getUserFromAuth = (authHeader) => {
  if (!authHeader || !authHeader.startsWith("Bearer ")) return null;
  const token = authHeader.split(" ")[1];
  const session = sessions.find((s) => s.access_token === token && !s.revoked);
  if (!session) return null;
  const user = users.find((u) => u.id === session.user_id);
  if (!user) return null;
  return { user, session };
};

const getUserSafe = (user) => ({
  id: user.id,
  name: user.name,
  email: user.email,
  cpf: user.cpf,
  address: user.address,
  is_admin: !!user.is_admin,
});

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return respond(200, { message: "ok" });
  }

  const route = ((event.path || "").replace(/^\/\.netlify\/functions\/store/, "") || "/").replace(/\/\/+/, "/");
  const method = event.httpMethod;
  const query = event.queryStringParameters || {};
  let body = {};

  try {
    if (event.body) {
      body = JSON.parse(event.body);
    }
  } catch (err) {
    return respond(400, { error: "Corpo JSON inválido" });
  }

  const auth = getUserFromAuth(event.headers.Authorization || event.headers.authorization);

  if (route === "/api/products" && method === "GET") {
    return respond(200, { products, categories: getCategories() });
  }

  if (route.startsWith("/api/products/") && method === "GET") {
    const id = parseInt(route.split("/").pop(), 10);
    const product = products.find((p) => p.id === id);
    if (!product) return respond(404, { error: "Produto não encontrado" });
    return respond(200, product);
  }

  if (route === "/api/shipping" && method === "GET") {
    const zip = query.zip || "";
    const subtotal = parseFloat(query.subtotal || "0") || 0;
    const shipping = calcShipping(zip);
    const free = subtotal >= 199;
    return respond(200, {
      price: free ? 0.0 : shipping.price,
      original_price: shipping.price,
      days: shipping.days,
      state: shipping.state,
      free_shipping_eligible: free,
    });
  }

  if (route === "/api/coupons" && method === "GET") {
    const code = (query.code || "").toUpperCase();
    const subtotal = parseFloat(query.subtotal || "0") || 0;
    const cp = coupons[code];
    if (!cp) return respond(200, { valid: false, message: "Cupom inválido" });
    if (subtotal < cp.min_value) {
      return respond(200, { valid: false, message: `Compra mínima: R$ ${cp.min_value.toFixed(2)}` });
    }
    return respond(200, { valid: true, coupon: { code, ...cp } });
  }

  if (route === "/api/tips" && method === "GET") {
    const tip = learningTips[Math.floor(Math.random() * learningTips.length)];
    return respond(200, { tip });
  }

  if (route === "/api/quiz" && method === "GET") {
    const question = quizQuestions[Math.floor(Math.random() * quizQuestions.length)];
    return respond(200, { question: { id: question.id, prompt: question.prompt, options: question.options } });
  }

  if (route === "/api/quiz/answer" && method === "POST") {
    const question = quizQuestions.find((q) => q.id === body.question_id);
    if (!question) return respond(404, { error: "Pergunta não encontrada" });
    const correct = body.selected === question.correct_index;
    return respond(200, {
      correct,
      correct_index: question.correct_index,
      explanation: question.explanation,
    });
  }

  if (route === "/api/login" && method === "POST") {
    const email = (body.email || "").trim().toLowerCase();
    const password = body.password || "";
    const user = users.find((u) => u.email === email);
    if (!user || user.password_hash !== hashPassword(password)) {
      return respond(401, { error: "Credenciais inválidas" });
    }
    const access_token = generateToken();
    const refresh_token = generateToken();
    sessions.push({ user_id: user.id, access_token, refresh_token, revoked: false, created_at: Date.now() });
    return respond(200, { access_token, refresh_token, user: getUserSafe(user) });
  }

  if (route === "/api/register" && method === "POST") {
    const name = (body.name || "").trim();
    const email = (body.email || "").trim().toLowerCase();
    const password = body.password || "";
    const cpf = (body.cpf || "").trim();
    const address = (body.address || "").trim();
    if (!name || !email || !password || !cpf || !address) {
      return respond(400, { error: "Preencha todos os campos" });
    }
    if (users.some((u) => u.email === email)) {
      return respond(400, { error: "E-mail já cadastrado" });
    }
    const user = { id: nextUserId++, name, email, password_hash: hashPassword(password), cpf, address, is_admin: false };
    users.push(user);
    const access_token = generateToken();
    const refresh_token = generateToken();
    sessions.push({ user_id: user.id, access_token, refresh_token, revoked: false, created_at: Date.now() });
    return respond(201, { access_token, refresh_token, user: getUserSafe(user) });
  }

  if (route === "/api/logout" && method === "POST") {
    if (!auth) return respond(200, { message: "Logout efetuado" });
    auth.session.revoked = true;
    return respond(200, { message: "Logout efetuado" });
  }

  if (route === "/api/me" && method === "GET") {
    if (!auth) return respond(401, { error: "Não autenticado" });
    return respond(200, { user: getUserSafe(auth.user) });
  }

  if (route === "/api/orders" && method === "POST") {
    if (!auth) return respond(401, { error: "Autenticação necessária" });
    if (!Array.isArray(body.items) || !body.items.length) {
      return respond(400, { error: "Dados inválidos" });
    }
    const customer = body.customer || {};
    const items = [];
    let subtotalItems = 0;
    for (const item of body.items) {
      const product = products.find((p) => p.id === item.id);
      if (!product) return respond(400, { error: `Produto ${item.id} não encontrado` });
      const qty = Math.max(1, parseInt(item.qty, 10) || 1);
      if (qty > product.stock) return respond(400, { error: `Estoque insuficiente para ${product.name}` });
      const subtotal = product.price * qty;
      items.push({ product, qty, subtotal });
      subtotalItems += subtotal;
    }
    let discount = 0;
    let couponCode = null;
    const couponCodeRequested = (body.coupon || "").trim().toUpperCase();
    if (couponCodeRequested && coupons[couponCodeRequested]) {
      const coupon = coupons[couponCodeRequested];
      if (subtotalItems >= coupon.min_value) {
        if (coupon.type === "percent") discount = (subtotalItems * coupon.discount) / 100;
        else discount = coupon.discount;
        couponCode = couponCodeRequested;
      }
    }
    const shipping = calcShipping(customer.zip || "").price;
    const shippingPrice = subtotalItems >= 199 ? 0 : shipping;
    const total = Math.round((subtotalItems - discount + shippingPrice) * 100) / 100;
    const pix_code = generatePixCode();
    const pix_expires_at = new Date(Date.now() + 30 * 60 * 1000).toISOString();
    const order = {
      id: nextOrderId++,
      customer_name: auth.user.name,
      customer_email: auth.user.email,
      customer_cpf: auth.user.cpf,
      customer_address: auth.user.address,
      customer_zip: customer.zip || "",
      subtotal: Math.round(subtotalItems * 100) / 100,
      discount: Math.round(discount * 100) / 100,
      shipping: Math.round(shippingPrice * 100) / 100,
      shipping_days: calcShipping(customer.zip || "").days,
      total,
      coupon_code: couponCode,
      payment: body.payment || "pix",
      pix_code,
      pix_expires_at,
      created_at: new Date().toISOString(),
      status: "pending_payment",
      items: items.map((it) => ({ product_id: it.product.id, name: it.product.name, qty: it.qty, price: it.product.price, subtotal: Math.round(it.subtotal * 100) / 100 })),
      user_id: auth.user.id,
    };
    orders.push(order);
    return respond(201, {
      order_id: order.id,
      total: order.total,
      pix_code: order.pix_code,
      pix_expires_at: order.pix_expires_at,
      message: "Pedido criado! Aguardando pagamento.",
    });
  }

  if (route.startsWith("/api/orders/") && method === "GET") {
    const id = parseInt(route.split("/").pop(), 10);
    const order = orders.find((o) => o.id === id);
    if (!order) return respond(404, { error: "Pedido não encontrado" });
    return respond(200, order);
  }

  return respond(404, { error: "Rota não encontrada" });
};
