import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 5 },  // Ramp-up to 5 concurrent users
    { duration: '30s', target: 10 }, // Sustained load at 10 concurrent users
    { duration: '15s', target: 0 },  // Graceful ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1500'], // 95% of audit responses under 1.5s
    http_req_failed: ['rate<0.01'],    // Failure rate under 1%
  },
};

const payload = JSON.stringify({
  shipment_id: 'SHP-K6-BENCHMARK',
  importer: 'PT Nexus Indo Tech',
  carrier: 'CMA CGM',
  destination_port: 'Tanjung Priok, Jakarta (IDTPP)',
  container_count: 2,
  items: [
    {
      item_id: 1,
      declared_description: 'Industrial Air Compressor 500L',
      declared_hs_code: '8414.80',
      quantity: 1,
      unit_price: 25000.0,
      total_value: 25000.0,
    },
    {
      item_id: 2,
      declared_description: 'Apple iPhone 15 Pro Max 256GB Dual SIM Phone',
      declared_hs_code: '8517.13',
      quantity: 100,
      unit_price: 1150.0,
      total_value: 115000.0,
    },
  ],
});

const params = {
  headers: {
    'Content-Type': 'application/json',
  },
};

export default function () {
  const res = http.post('http://localhost:8000/api/v1/audit', payload, params);

  check(res, {
    'audit status is 200': (r) => r.status === 200,
    'audit payload returned overall_status': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Boolean(body && (body.overall_status !== undefined || (body.audit && body.audit.overall_status !== undefined)));
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);
}
