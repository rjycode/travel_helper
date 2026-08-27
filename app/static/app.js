/* 旅游数据演示台 - 前端逻辑 */
const { createApp } = Vue;

const API = '';

function today(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

createApp({
  data() {
    return {
      tab: 'products',
      tabs: [
        { key: 'products', label: '商品' },
        { key: 'orders', label: '订单' },
        { key: 'coupons', label: '优惠券' },
        { key: 'me', label: '我的' },
      ],
      productTabs: [
        { key: 'hotel', label: '酒店' },
        { key: 'scenic', label: '景点' },
        { key: 'flight', label: '机票' },
        { key: 'train', label: '火车票' },
        { key: 'bus', label: '汽车票' },
        { key: 'transfer', label: '接送' },
      ],
      prodTab: 'hotel',

      userId: 1,
      demoUsers: [],
      areas: [],

      // 搜索条件
      hotelQ: { areaId: null, checkIn: today(1), checkOut: today(2), stars: '', keyword: '' },
      scenicQ: { areaId: null, travelDate: today(1), ratings: '', keyword: '' },
      flightQ: { from: null, to: null, date: today(1), cabin: '' },
      trainQ: { from: null, to: null, date: today(1), seat: '' },
      busQ: { from: null, to: null, date: today(1) },
      transferQ: { areaId: null, date: today(1), type: '' },

      // 结果
      hotels: [], scenics: [], flights: [], trains: [], buses: [], transfers: [],

      // 弹窗
      modal: null, modalType: '', modalData: {}, modalTitle: '',
      orderModal: false, orderDraft: {},
      detailModal: false, detail: {},
      payModal: false,
      refundModal: false,
      travelerModal: null,

      // 订单/优惠券/我的
      orders: [],
      orderQ: { status: '', type: '' },
      availableTemplates: [], myCoupons: [],
      me: {}, account: {}, ledger: [], showLedger: false,
      travelers: [],
      usableCoupons: [],

      toast: null, toastTimer: null,
    };
  },

  computed: {
    areaNameMap() {
      const m = {};
      for (const a of this.areas) m[a.areaId] = a.areaName;
      return m;
    },
  },

  mounted() {
    this.init();
  },

  methods: {
    // ===== 基础 =====
    fmt(v) {
      return (v == null ? 0 : Number(v)).toFixed(2);
    },
    typeName(kind, code) {
      const maps = {
        hotel: { luxury: '豪华型', business: '商务型', resort: '度假型', boutique: '精品型' },
        scenic: {
          theme_park: '主题公园', museum: '博物馆', mountain: '山地', heritage: '文化遗产',
          wetland: '湿地', beach: '海滨', snow: '冰雪', forest: '森林', waterfall: '瀑布',
          cultural_square: '文化广场', ancient_town: '古镇', religious: '宗教', theme_water: '水乐园',
          zoo: '动物园', botanical_garden: '植物园', industrial_tourism: '工业旅游',
          red_tourism: '红色旅游', ecological: '生态景区',
        },
        transfer: { airport_pickup: '机场接机', airport_dropoff: '机场送机', charter_daily: '包车一日游', station_transfer: '车站接送' },
        vehicle: { economy: '经济型', comfort: '舒适型', business: '商务型', van: '商务车' },
        order: {
          hotel_room: '酒店', scenic_ticket: '景点门票', flight_cabin: '机票',
          train_seat: '火车票', bus_seat: '汽车票', transfer_service: '接送服务',
        },
      };
      return (maps[kind] || {})[code] || code;
    },
    statusName(code) {
      const m = {
        pending_payment: '待支付', cancelled: '已取消', paid: '已支付', in_progress: '进行中',
        finished: '已完成', ticketed: '已出票', refunded: '已退款', completed: '已完成',
        pending: '待处理', approved: '已通过', rejected: '已驳回', success: '成功',
        available: '可用', used: '已使用', expired: '已过期', active: '有效', inactive: '无效',
      };
      return m[code] || code;
    },
    seatName(code) {
      return { second_class: '二等座', first_class: '一等座', business: '商务座', coach: '大巴' }[code] || code;
    },
    levelName(code) {
      return { normal: '普通会员', silver: '银卡会员', gold: '金卡会员' }[code] || code;
    },
    ledgerName(code) {
      const m = {
        signup_bonus: '注册奖励', order_earn: '消费获积分', order_earn_revoke: '退款撤销积分',
        point_redeem: '积分抵扣', expire: '过期清零', admin_adjust: '管理员调整',
      };
      return m[code] || code;
    },
    toastMsg(msg, type = 'info') {
      this.toast = { msg, type };
      clearTimeout(this.toastTimer);
      this.toastTimer = setTimeout(() => (this.toast = null), 2600);
    },

    // ===== 请求 =====
    async api(method, path, body = null, extraHeaders = {}) {
      const headers = { 'Content-Type': 'application/json', ...extraHeaders };
      const resp = await fetch(API + path, {
        method,
        headers,
        body: body != null ? JSON.stringify(body) : undefined,
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        const msg = data.detail || data.message || `HTTP ${resp.status}`;
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
      return data;
    },
    auth() {
      return { 'X-User-Id': String(this.userId) };
    },

    // ===== 初始化 =====
    async init() {
      try {
        const [users, areas] = await Promise.all([
          this.api('GET', '/api/v1/demo/users?limit=50'),
          this.api('GET', '/api/v1/demo/areas?limit=500'),
        ]);
        this.demoUsers = users.list;
        this.areas = areas.list;
        if (this.demoUsers.length) this.userId = this.demoUsers[0].userId;
        // 默认搜索城市取第一个有数据的
        this.hotelQ.areaId = this.areas.length ? this.areas[0].areaId : null;
        this.scenicQ.areaId = this.hotelQ.areaId;
        this.flightQ.from = this.hotelQ.areaId;
        this.flightQ.to = this.areas.length > 1 ? this.areas[1].areaId : this.hotelQ.areaId;
        this.trainQ.from = this.hotelQ.areaId;
        this.trainQ.to = this.areas.length > 1 ? this.areas[1].areaId : this.hotelQ.areaId;
        this.busQ.from = this.hotelQ.areaId;
        this.busQ.to = this.areas.length > 1 ? this.areas[1].areaId : this.hotelQ.areaId;
        this.transferQ.areaId = this.hotelQ.areaId;
        await this.searchHotels();
        await this.onUserSwitch();
      } catch (e) {
        this.toastMsg('初始化失败：' + e.message, 'error');
      }
    },

    async onUserSwitch() {
      try {
        await Promise.all([
          this.loadMe(),
          this.loadOrders(),
          this.loadCoupons(),
          this.loadTravelers(),
          this.loadMember(),
        ]);
      } catch (e) {
        this.toastMsg(e.message, 'error');
      }
    },

    switchProdTab(key) {
      this.prodTab = key;
      const map = {
        hotel: this.searchHotels, scenic: this.searchScenics, flight: this.searchFlights,
        train: this.searchTrains, bus: this.searchBuses, transfer: this.searchTransfers,
      };
      map[key]();
    },

    // ===== 商品搜索 =====
    async searchHotels() {
      const q = this.hotelQ;
      if (!q.areaId || !q.checkIn || !q.checkOut) return;
      const params = new URLSearchParams({
        areaId: q.areaId, checkInDate: q.checkIn, checkOutDate: q.checkOut, pageSize: 30,
      });
      if (q.stars) params.append('starRatingCodes', q.stars);
      if (q.keyword) params.append('keyword', q.keyword);
      try {
        const d = await this.api('GET', '/api/v1/hotels?' + params);
        this.hotels = d.list;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async searchScenics() {
      const q = this.scenicQ;
      if (!q.areaId || !q.travelDate) return;
      const params = new URLSearchParams({ areaId: q.areaId, travelDate: q.travelDate, pageSize: 30 });
      if (q.ratings) params.append('ratingCodes', q.ratings);
      if (q.keyword) params.append('keyword', q.keyword);
      try {
        const d = await this.api('GET', '/api/v1/scenic-spots?' + params);
        this.scenics = d.list;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async searchFlights() {
      const q = this.flightQ;
      if (!q.from || !q.to || !q.date) return;
      const params = new URLSearchParams({ departureAreaId: q.from, arrivalAreaId: q.to, departureDate: q.date, pageSize: 30 });
      if (q.cabin) params.append('cabinClassCodes', q.cabin);
      try {
        const d = await this.api('GET', '/api/v1/flights/search?' + params);
        this.flights = d.list;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async searchTrains() {
      const q = this.trainQ;
      if (!q.from || !q.to || !q.date) return;
      const params = new URLSearchParams({ departureAreaId: q.from, arrivalAreaId: q.to, departureDate: q.date, pageSize: 30 });
      if (q.seat) params.append('seatClassCodes', q.seat);
      try {
        const d = await this.api('GET', '/api/v1/trains/search?' + params);
        this.trains = d.list;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async searchBuses() {
      const q = this.busQ;
      if (!q.from || !q.to || !q.date) return;
      const params = new URLSearchParams({ departureAreaId: q.from, arrivalAreaId: q.to, departureDate: q.date, pageSize: 30 });
      try {
        const d = await this.api('GET', '/api/v1/buses/search?' + params);
        this.buses = d.list;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async searchTransfers() {
      const q = this.transferQ;
      if (!q.areaId || !q.date) return;
      const params = new URLSearchParams({ areaId: q.areaId, businessDate: q.date, pageSize: 30 });
      if (q.type) params.append('serviceTypeCodes', q.type);
      try {
        const d = await this.api('GET', '/api/v1/transfers?' + params);
        this.transfers = d.list;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },

    // ===== 商品详情弹窗 =====
    async openHotel(h) {
      try {
        const [detail, rt] = await Promise.all([
          this.api('GET', `/api/v1/hotels/${h.hotelId}`),
          this.api('GET', `/api/v1/hotels/${h.hotelId}/room-types?checkInDate=${this.hotelQ.checkIn}&checkOutDate=${this.hotelQ.checkOut}`),
        ]);
        this.modalType = 'hotel';
        this.modalData = { ...detail, roomTypes: rt.list };
        this.modalTitle = detail.hotelName;
        this.modal = true;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async openScenic(s) {
      try {
        const [detail, tt] = await Promise.all([
          this.api('GET', `/api/v1/scenic-spots/${s.scenicSpotId}`),
          this.api('GET', `/api/v1/scenic-spots/${s.scenicSpotId}/ticket-types?travelDate=${this.scenicQ.travelDate}`),
        ]);
        this.modalType = 'scenic';
        this.modalData = { ...detail, ticketTypes: tt.list };
        this.modalTitle = detail.scenicName;
        this.modal = true;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async openFlight(f) {
      try {
        const d = await this.api('GET', `/api/v1/flights/${f.departureId}`);
        this.modalType = 'flight';
        this.modalData = d;
        this.modalTitle = `${d.airlineCode} ${d.flightNo} ${d.departureTime.slice(0, 16)}`;
        this.modal = true;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async openTrain(t) {
      try {
        const d = await this.api('GET', `/api/v1/trains/${t.departureId}`);
        this.modalType = 'train';
        this.modalData = d;
        this.modalTitle = `${d.trainNo} ${d.departureTime.slice(0, 16)}`;
        this.modal = true;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async openBus(b) {
      try {
        const d = await this.api('GET', `/api/v1/buses/${b.departureId}`);
        this.modalType = 'bus';
        this.modalData = d;
        this.modalTitle = `${d.routeName} ${d.departureTime.slice(0, 16)}`;
        this.modal = true;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async openTransfer(t) {
      try {
        const areas = this.areas;
        const pickup = areas[Math.floor(areas.length / 2)] || areas[0];
        const dropoff = areas[0];
        const d = await this.api('GET',
          `/api/v1/transfers/${t.serviceId}/pricing?pickupAreaId=${pickup.areaId}&dropoffAreaId=${dropoff.areaId}&businessDate=${this.transferQ.date}`);
        this.modalType = 'transfer';
        this.modalData = { ...d, serviceName: t.serviceName };
        this.modalTitle = t.serviceName;
        this.modal = true;
      } catch (e) {
        // 该上下车组合可能无规则，尝试默认组合
        this.toastMsg('该服务暂无可用的上下车组合报价', 'error');
      }
    },

    // ===== 下单 =====
    async prepareOrderDraft(type, payload) {
      this.orderDraft = {
        type,
        productTypeCode: type,
        productId: payload.productId,
        productName: payload.productName,
        unitPrice: payload.unitPrice,
        checkIn: this.hotelQ.checkIn,
        checkOut: this.hotelQ.checkOut,
        travelerId: '',
        couponId: '',
        usePoints: false,
        extra: payload,
      };
      // 交通类必须选出行人
      if (['flight_cabin', 'train_seat', 'bus_seat'].includes(type)) {
        if (!this.travelers.length) {
          this.toastMsg('请先在"我的"页添加常用出行人', 'error');
          return false;
        }
        this.orderDraft.travelerId = this.travelers[0].travelerId;
      }
      // 可用的券（按商品类型过滤）
      const productTypeMap = {
        hotel_room: 'hotel_room', scenic_ticket: 'scenic_ticket', flight_cabin: 'flight_cabin',
        train_seat: 'train_seat', bus_seat: 'bus_seat', transfer_service: 'transfer_service',
      };
      const pt = productTypeMap[type];
      this.usableCoupons = this.myCoupons.filter(
        (c) => c.statusCode === 'available' && c.applicableProductType === pt,
      );
      this.modal = null; // 关闭商品详情弹窗
      this.orderModal = true;
      return true;
    },
    buyHotel(rt) {
      this.prepareOrderDraft('hotel_room', {
        productId: rt.roomTypeId,
        productName: this.modalData.hotelName + '-' + rt.roomTypeName,
        unitPrice: rt.firstNightSalePriceAmount,
      });
    },
    buyScenic(t) {
      this.prepareOrderDraft('scenic_ticket', {
        productId: t.ticketTypeId,
        productName: this.modalData.scenicName + '-' + t.ticketTypeName,
        unitPrice: t.salePriceAmount,
        travelDate: this.scenicQ.travelDate,
      });
    },
    buyFlight(c) {
      this.prepareOrderDraft('flight_cabin', {
        productId: c.cabinId,
        productName: `${this.modalData.airlineCode} ${this.modalData.flightNo} ${c.cabinClassCode === 'economy' ? '经济舱' : '商务舱'}`,
        unitPrice: c.salePriceAmount,
        travelTime: this.modalData.departureTime,
        productTypeCode: 'flight_cabin',
      });
    },
    buyTrain(s) {
      this.prepareOrderDraft('train_seat', {
        productId: s.seatId,
        productName: `${this.modalData.trainNo} ${this.seatName(s.seatClassCode)}`,
        unitPrice: s.salePriceAmount,
        travelTime: this.modalData.departureTime,
        productTypeCode: 'train_seat',
      });
    },
    buyBus(s) {
      this.prepareOrderDraft('bus_seat', {
        productId: s.seatId,
        productName: `${this.modalData.routeName} 大巴座`,
        unitPrice: s.salePriceAmount,
        travelTime: this.modalData.departureTime,
        productTypeCode: 'bus_seat',
      });
    },
    buyTransfer() {
      this.prepareOrderDraft('transfer_service', {
        productId: this.modalData.serviceId,
        productName: this.modalData.serviceName,
        unitPrice: this.modalData.salePriceAmount,
        travelTime: this.transferQ.date,
        productTypeCode: 'transfer_service',
      });
    },

    async createOrder() {
      const d = this.orderDraft;
      const items = [{
        productTypeCode: d.productTypeCode,
        productId: d.productId,
        productName: d.productName,
        quantity: 1,
      }];
      if (d.type === 'hotel_room') {
        items[0].checkInDate = d.checkIn;
        items[0].checkOutDate = d.checkOut;
      }
      if (d.travelerId) items[0].travelerIds = [d.travelerId];
      // 非酒店商品：传出行时间（从详情快照取）
      if (d.type !== 'hotel_room') {
        const tt = d.extra && (d.extra.travelTime || d.extra.travelDate);
        if (tt) items[0].travelTime = String(tt).replace('T', ' ');
      }
      const body = {
        orderTypeCode: d.productTypeCode,
        sourceChannelCode: 'app',
        currencyCode: 'CNY',
        items,
        userCouponIds: d.couponId ? [d.couponId] : [],
        usePoints: d.usePoints,
      };
      try {
        const order = await this.api('POST', '/api/v1/orders', body, this.auth());
        this.orderModal = false;
        this.toastMsg(`订单创建成功：${order.orderNo}`, 'success');
        await this.loadOrders();
        this.detail = await this.api('GET', `/api/v1/orders/${order.orderId}`, null, this.auth());
        this.detailModal = true;
      } catch (e) {
        this.toastMsg('下单失败：' + e.message, 'error');
      }
    },

    // ===== 订单 =====
    async loadOrders() {
      const params = new URLSearchParams({ pageSize: 30 });
      if (this.orderQ.status) params.append('statusCode', this.orderQ.status);
      if (this.orderQ.type) params.append('orderTypeCode', this.orderQ.type);
      const d = await this.api('GET', '/api/v1/orders?' + params, null, this.auth());
      this.orders = d.list;
    },
    async openOrder(o) {
      try {
        this.detail = await this.api('GET', `/api/v1/orders/${o.orderId}`, null, this.auth());
        // 补充退款申请列表
        try {
          const rrs = await this.api('GET', '/api/v1/refund-requests?pageSize=100', null, this.auth());
          this.detail.refundRequests = rrs.list.filter((r) => r.orderId === o.orderId);
        } catch (e) { this.detail.refundRequests = []; }
        this.detailModal = true;
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async cancelOrder(o) {
      try {
        const r = await this.api('POST', `/api/v1/orders/${o.orderId}/cancel`, { cancelReason: '用户主动取消' }, this.auth());
        this.toastMsg('订单已取消', 'success');
        this.detailModal = false;
        await this.loadOrders();
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async payOrder(o) {
      this.payModal = { order: o, method: 'alipay', payment: null, paying: false };
    },
    async confirmPay() {
      const pm = this.payModal;
      if (!pm || pm.paying) return;
      pm.paying = true;
      try {
        const p = await this.api('POST', `/api/v1/orders/${pm.order.orderId}/payments`,
          { paymentMethodCode: pm.method, clientType: 'web' }, this.auth());
        pm.payment = p;
        // 模拟回调（演示环境）
        const cb = await this.api('POST', '/api/v1/payments/callback', {
          paymentNo: p.paymentNo,
          orderId: pm.order.orderId,
          paymentMethodCode: pm.method,
          amount: p.amount,
          statusCode: 'success',
          paidAt: new Date().toISOString().slice(0, 19).replace('T', ' '),
          channelTradeNo: 'MOCK_' + p.paymentNo,
        }, { 'X-Demo-Payment-Signature': 'mock-payment-signature' });
        this.toastMsg(`支付成功！订单状态：${this.statusName(cb.orderStatusCode)}`, 'success');
        this.payModal = false;
        this.detailModal = false;
        await Promise.all([this.loadOrders(), this.loadMember()]);
      } catch (e) {
        this.toastMsg('支付失败：' + e.message, 'error');
      } finally {
        pm.paying = false;
      }
    },

    // ===== 退款 =====
    openRefund(detail) {
      const items = detail.items
        .filter((it) => ['paid', 'ticketed', 'in_progress'].includes(it.statusCode) || it.statusCode === 'paid')
        .map((it) => ({ ...it, _refundAmt: Number(it.saleAmount) }));
      if (!items.length) {
        this.toastMsg('没有可退款的明细', 'error');
        return;
      }
      this.refundModal = { orderId: detail.orderId, items, reason: '行程变更' };
    },
    async submitRefund() {
      const rm = this.refundModal;
      try {
        for (const it of rm.items) {
          if (!it._refundAmt || Number(it._refundAmt) <= 0) continue;
          await this.api('POST', `/api/v1/orders/${rm.orderId}/items/${it.orderItemId}/refund-requests`,
            { requestedAmount: Number(it._refundAmt), reason: rm.reason }, this.auth());
        }
        this.toastMsg('退款申请已提交', 'success');
        this.refundModal = false;
        this.detailModal = false;
        await Promise.all([this.loadOrders(), this.loadMember()]);
      } catch (e) {
        this.toastMsg('退款申请失败：' + e.message, 'error');
      }
    },

    // ===== 优惠券 =====
    async loadCoupons() {
      const [tpl, mine] = await Promise.all([
        this.api('GET', '/api/v1/coupon-templates/available?pageSize=50', null, this.auth()),
        this.api('GET', '/api/v1/coupons?pageSize=100', null, this.auth()),
      ]);
      this.availableTemplates = tpl.list;
      this.myCoupons = mine.list;
    },
    async receiveCoupon(t) {
      try {
        const r = await this.api('POST', '/api/v1/coupons/receive', { templateId: t.templateId }, this.auth());
        this.toastMsg('领取成功', 'success');
        await this.loadCoupons();
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },

    // ===== 我的 =====
    async loadMe() {
      this.me = await this.api('GET', '/api/v1/me', null, this.auth());
    },
    async loadMember() {
      this.account = await this.api('GET', '/api/v1/me/member-account', null, this.auth());
    },
    async loadLedger() {
      this.ledger = (await this.api('GET', '/api/v1/me/point-ledger?pageSize=50', null, this.auth())).list;
    },
    async toggleLedger() {
      if (!this.showLedger) {
        this.ledger = (await this.api('GET', '/api/v1/me/point-ledger?pageSize=50', null, this.auth())).list;
      }
      this.showLedger = !this.showLedger;
    },
    async loadTravelers() {
      this.travelers = (await this.api('GET', '/api/v1/me/travelers?pageSize=100', null, this.auth())).list;
    },
    async openTravelerEdit(t) {
      this.travelerModal = t ? {
        id: t.travelerId, name: t.travelerName, idType: t.identityTypeCode,
        idNo: '', phone: t.phone, gender: t.genderCode, birth: t.birthDate,
      } : {
        id: null, name: '', idType: 'id_card', idNo: '', phone: '', gender: 'male', birth: '1995-01-01',
      };
    },
    async saveTraveler() {
      const m = this.travelerModal;
      if (!m.name || !m.idNo) { this.toastMsg('姓名和证件号必填', 'error'); return; }
      const body = {
        travelerName: m.name,
        identityTypeCode: m.idType,
        identityNo: m.idNo,
        genderCode: m.gender,
        birthDate: m.birth,
        phone: m.phone,
      };
      try {
        if (m.id) {
          await this.api('PUT', `/api/v1/me/travelers/${m.id}`, { ...body, statusCode: 'active' }, this.auth());
          this.toastMsg('出行人已更新', 'success');
        } else {
          await this.api('POST', '/api/v1/me/travelers', body, this.auth());
          this.toastMsg('出行人已新增', 'success');
        }
        this.travelerModal = false;
        await this.loadTravelers();
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
    async deactivateTraveler(t) {
      try {
        await this.api('DELETE', `/api/v1/me/travelers/${t.travelerId}`, null, this.auth());
        this.toastMsg('出行人已停用', 'success');
        await this.loadTravelers();
      } catch (e) { this.toastMsg(e.message, 'error'); }
    },
  },
}).mount('#app');
