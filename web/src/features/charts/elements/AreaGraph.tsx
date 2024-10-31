import { ScaleLinear, scaleLinear } from 'd3-scale';
import { Series, stack, stackOffsetDiverging } from 'd3-shape';
import { add } from 'date-fns';
import TimeAxis from 'features/time/TimeAxis';
import { useHeaderHeight } from 'hooks/headerHeight';
import { atom, useAtom, useAtomValue } from 'jotai';
import React, { useMemo, useRef, useState } from 'react';
import { ZoneDetail } from 'types';
import useResizeObserver from 'use-resize-observer';
import { TimeAverages, timeAxisMapping } from 'utils/constants';
import { getZoneTimezone, useGetZoneFromPath } from 'utils/helpers';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import { getTimeScale } from '../graphUtils';
import AreaGraphTooltip from '../tooltips/AreaGraphTooltip';
import { AreaGraphElement, FillFunction, InnerAreaGraphTooltipProps } from '../types';
import AreaGraphLayers from './AreaGraphLayers';
import GraphBackground from './GraphBackground';
import GraphHoverLine from './GraphHoverline';
import ValueAxis from './ValueAxis';

const X_AXIS_HEIGHT = 20;
const Y_AXIS_WIDTH = 26;
const Y_AXIS_PADDING = 2;

interface Layer {
  key: string;
  stroke: string;
  fill: string | ((d: { data: AreaGraphElement }) => string);
  markerFill: string | ((d: { data: AreaGraphElement }) => string);
  datapoints: Series<AreaGraphElement, string>;
}

const getTotalValues = (layers: Layer[]): { min: number; max: number } => {
  // Use a single loop to find the min and max values of the datapoints
  let min = 0;
  let max = 0;
  for (const layer of layers) {
    for (const [low, high] of layer.datapoints) {
      // Check if the values are finite numbers
      if (Number.isFinite(low)) {
        min = Math.min(min, low);
      }
      if (Number.isFinite(high)) {
        max = Math.max(max, high);
      }
    }
  }
  // Return the min and max values
  return {
    min: min,
    max: max,
  };
};

const getValueScale = (
  height: number,
  totalValues: { min: number; max: number }
): ScaleLinear<number, number> =>
  scaleLinear()
    .domain([Math.min(0, 1.1 * totalValues.min), Math.max(0, 1.1 * totalValues.max)])
    .range([height, Y_AXIS_PADDING]);

const getLayers = (
  data: AreaGraphElement[],
  layerKeys: string[],
  layerFill: FillFunction,
  markerFill?: FillFunction,
  layerStroke?: (key: string) => string
): Layer[] => {
  if (!data || !data[0]) {
    return [];
  }

  const stackedData = stack<AreaGraphElement>()
    .offset(stackOffsetDiverging)
    .value((d: AreaGraphElement, key: string) =>
      Number.isNaN(d.layerData[key]) ? 0 : d.layerData[key]
    ) // Assign 0 if no data
    .keys(layerKeys)(data);

  return layerKeys.map((key: string, index: number) => ({
    key,
    stroke: layerStroke ? layerStroke(key) : 'none',
    fill: layerFill(key),
    markerFill: markerFill ? markerFill(key) : layerFill(key),
    datapoints: stackedData[index],
  }));
};

interface AreagraphProps {
  data: AreaGraphElement[];
  testId: string;
  layerKeys: string[];
  layerStroke?: (key: string) => string;
  layerFill: FillFunction;
  markerFill?: FillFunction;
  markerUpdateHandler: (
    position: { x: number; y: number },
    dataPoint: AreaGraphElement
  ) => void;
  markerHideHandler: () => void;
  isMobile: boolean;
  isDisabled?: boolean;
  height: string;
  datetimes: Date[];
  selectedTimeAggregate: TimeAverages; // TODO: Graph does not need to know about this
  tooltip: (props: InnerAreaGraphTooltipProps) => JSX.Element | null;
  tooltipSize?: 'small' | 'large';
  formatTick?: (t: number) => string | number;
  showHoverHighlight?: boolean;
}

interface TooltipData {
  position: { x: number; y: number };
  zoneDetail: ZoneDetail;
}

const AreaGraphIndexSelectedAtom = atom<number | null>(null);

function AreaGraph({
  data,
  testId,
  layerKeys,
  layerStroke,
  layerFill,
  markerFill,
  isMobile,
  height = '10em',
  isDisabled = false,
  selectedTimeAggregate,
  datetimes,
  tooltip,
  tooltipSize,
  formatTick = String,
  showHoverHighlight,
}: AreagraphProps) {
  const reference = useRef(null);
  const { width: observerWidth = 0, height: observerHeight = 0 } =
    useResizeObserver<HTMLDivElement>({ ref: reference });

  const selectedDate = useAtomValue(selectedDatetimeIndexAtom);
  const [tooltipData, setTooltipData] = useState<TooltipData | null>(null);
  const isBiggerThanMobile = useBreakpoint('sm');
  const zoneId = useGetZoneFromPath();
  const zoneTimezone = getZoneTimezone(zoneId);

  const containerWidth = Math.max(observerWidth - Y_AXIS_WIDTH, 0);
  const containerHeight = Math.max(observerHeight - X_AXIS_HEIGHT, 0);

  // Build layers
  const layers = useMemo(
    () => getLayers(data, layerKeys, layerFill, markerFill, layerStroke),
    [data, layerKeys, layerStroke, layerFill, markerFill]
  );

  // Generate graph scales
  const totalValues = useMemo(() => getTotalValues(layers), [layers]);
  const valueScale = useMemo(
    () => getValueScale(containerHeight, totalValues),
    [containerHeight, totalValues]
  );
  const startTime = datetimes.at(0);
  const lastTime = datetimes.at(-1);

  // The endTime needs to include the last interval so it can be shown
  const endTime = useMemo(() => {
    if (!lastTime) {
      return null;
    }

    const duration = timeAxisMapping[selectedTimeAggregate];

    //add exactly 1 interval to the last time, e.g. 1 hour or 1 day or 1 month, etc.
    return duration ? add(lastTime, { [duration]: 1 }) : null;
  }, [lastTime, selectedTimeAggregate]);

  const datetimesWithNext = useMemo(
    // The as Date[] assertion is needed because the filter removes the null values but typescript can't infer that
    // This can be inferred by typescript 5.5 and can be removed when we upgrade
    () => [...datetimes, endTime].filter(Boolean) as Date[],
    [datetimes, endTime]
  );

  const timeScale = useMemo(
    () => getTimeScale(containerWidth, startTime, endTime),
    [containerWidth, startTime, endTime]
  );

  const [graphIndex, setGraphIndex] = useAtom(AreaGraphIndexSelectedAtom);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState<number | null>(null);

  const hoverLineTimeIndex = graphIndex ?? selectedDate.index;

  // Graph update handlers. Used for tooltip data.
  const markerUpdateHandler = useMemo(
    () => (position: { x: number; y: number }, dataPoint: AreaGraphElement) => {
      setTooltipData({
        position,
        zoneDetail: dataPoint.meta,
      });
    },
    [setTooltipData]
  );
  const markerHideHandler = useMemo(
    () => () => {
      setTooltipData(null);
    },
    [setTooltipData]
  );

  // Mouse action handlers
  const mouseMoveHandler = useMemo(
    () => (timeIndex: number | null, layerIndex: number | null) => {
      setGraphIndex(timeIndex);
      if (layers.length <= 1) {
        // Select the first (and only) layer even when hovering over background
        setSelectedLayerIndex(0);
      } else {
        // use the selected layer (or undefined to hide the tooltips)
        setSelectedLayerIndex(layerIndex);
      }
    },
    [layers, setGraphIndex, setSelectedLayerIndex]
  );
  const mouseOutHandler = useMemo(
    () => () => {
      setGraphIndex(null);
      setSelectedLayerIndex(null);
    },
    [setGraphIndex, setSelectedLayerIndex]
  );

  const headerHeight = useHeaderHeight();

  // Don't render the graph if datetimes and datapoints are not in sync
  for (const layer of layers) {
    if (layer.datapoints.length !== datetimes.length) {
      console.error('Datetimes and datapoints are not in sync');
      return null;
    }
  }

  if (layers.every((layer) => layer.datapoints.every((d) => d[0] === 0 && d[1] === 0))) {
    // Don't render the graph if all datapoints are 0
    return null;
  }

  return (
    <div ref={reference}>
      <svg
        data-test-id={testId}
        height={height}
        className={`w-full overflow-visible ${
          isDisabled ? 'pointer-events-none blur' : ''
        }`}
      >
        {timeScale && reference.current && (
          <GraphBackground
            timeScale={timeScale}
            valueScale={valueScale}
            datetimes={datetimes}
            mouseMoveHandler={mouseMoveHandler}
            mouseOutHandler={mouseOutHandler}
            isMobile={isMobile}
            svgNode={reference.current}
          />
        )}
        <AreaGraphLayers
          showHoverHighlight={showHoverHighlight}
          layers={layers}
          datetimes={datetimesWithNext}
          timeScale={timeScale}
          valueScale={valueScale}
          mouseMoveHandler={mouseMoveHandler}
          mouseOutHandler={mouseOutHandler}
          isMobile={isMobile}
          svgNode={reference.current}
          selectedLayerIndex={selectedLayerIndex}
        />
        <TimeAxis
          isLoading={false}
          selectedTimeAggregate={selectedTimeAggregate}
          datetimes={datetimesWithNext}
          scaleWidth={containerWidth}
          transform={`translate(5 ${containerHeight})`}
          className="h-[22px] w-full overflow-visible opacity-50"
          timezone={zoneTimezone}
        />
        <ValueAxis scale={valueScale} width={containerWidth} formatTick={formatTick} />
        <GraphHoverLine
          layers={layers}
          timeScale={timeScale}
          valueScale={valueScale}
          datetimes={datetimes}
          endTime={endTime}
          markerUpdateHandler={markerUpdateHandler}
          markerHideHandler={markerHideHandler}
          selectedLayerIndex={selectedLayerIndex}
          selectedTimeIndex={hoverLineTimeIndex}
          svgNode={reference.current}
        />
        {tooltip && (
          <AreaGraphTooltip
            {...tooltipData}
            selectedLayerKey={
              selectedLayerIndex === null ? undefined : layerKeys[selectedLayerIndex]
            }
            tooltipSize={tooltipSize}
            isBiggerThanMobile={isBiggerThanMobile}
            headerHeight={headerHeight}
          >
            {(props) => tooltip(props)}
          </AreaGraphTooltip>
        )}
      </svg>
    </div>
  );
}

export default React.memo(AreaGraph);
