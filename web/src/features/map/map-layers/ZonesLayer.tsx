import { useTheme } from 'hooks/theme';
import { Layer, Source } from 'react-map-gl/maplibre';

import { ZONE_SOURCE } from '../Map';
import { useGetGeometries } from '../map-utils/getMapGrid';

export default function ZonesLayer() {
  const { worldGeometries } = useGetGeometries();
  const theme = useTheme();

  return (
    <Source id={ZONE_SOURCE} promoteId={'zoneId'} type="geojson" data={worldGeometries}>
      <Layer
        id="zones-clickable-layer"
        type="fill"
        paint={{
          'fill-color': [
            'coalesce',
            ['feature-state', 'color'],
            ['get', 'color'],
            theme.clickableFill,
          ],
        }}
      />
      <Layer
        id="zones-hoverable-layer"
        type="fill"
        paint={{
          'fill-color': '#FFFFFF',
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.3,
            0,
          ],
        }}
      />
      <Layer
        id="zones-selectable-layer"
        type="fill"
        paint={{
          'fill-color': [
            'coalesce',
            ['feature-state', 'color'],
            ['get', 'color'],
            theme.clickableFill,
          ],
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.7,
            0,
          ],
        }}
      />
      <Layer
        id="zones-border"
        type="line"
        paint={{
          'line-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            'white',
            theme.strokeColor,
          ],
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            theme.strokeWidth * 12,
            ['boolean', ['feature-state', 'hover'], false],
            theme.strokeWidth * 10,
            theme.strokeWidth,
          ],
        }}
      />
    </Source>
  );
}
