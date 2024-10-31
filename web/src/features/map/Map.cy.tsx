import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { TestProvider } from 'testing/testUtils';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';

import Map from './Map';

const zonesToTest = ['DE', 'FR', 'NL', 'NO-NO1', 'SE-SE1', 'CH', 'ES'];

type ZoneLayer = {
  id: string;
  type: string;
  source: string;
  paint: {
    'fill-color': any;
  };
  layout: any;
};

type ZonesSnapshot = {
  [zoneCode: string]: ZoneLayer;
};

const zonesSnapshot: ZonesSnapshot = {
  DE: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  FR: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  NL: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  'NO-NO1': {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  'SE-SE1': {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  CH: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
  ES: {
    id: 'zones-clickable-layer',
    type: 'fill',
    source: 'zones-clickable',
    paint: {
      'fill-color': {
        r: 0.478_431_372_549_019_63,
        g: 0.529_411_764_705_882_4,
        b: 0.552_941_176_470_588_3,
        a: 1,
      },
    },
    layout: {},
  },
};

const handleMapLoad = (map: any) => {
  const features = map.queryRenderedFeatures({ layers: ['zones-clickable-layer'] });
  assert.exists(features);
  assert.isArray(features);
  for (const zoneId of zonesToTest) {
    const zone = features.find((f: any) => f.properties?.zoneId === zoneId)?.layer;
    if (!zone) {
      throw new Error(`Zone with ID ${zoneId} not found.`);
    }
    assert.deepEqual(zone, zonesSnapshot[zoneId]);
  }
};

describe('Map Component', () => {
  it('should display loading state initially', () => {
    const queryClient = new QueryClient();

    cy.mount(
      <TestProvider
        initialValues={[
          [
            selectedDatetimeIndexAtom,
            {
              datetime: new Date('2022-12-05T08:00:00+00:00'),
              index: 0,
            },
          ],
        ]}
      >
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Map onMapLoad={handleMapLoad} />
          </BrowserRouter>
        </QueryClientProvider>
      </TestProvider>
    );
    cy.get('[data-test-id=exchange-layer]').should('be.visible');
    cy.get('[data-test-id=wind-layer]').should('exist');
    cy.get('.maplibregl-map').should('be.visible');
  });
});