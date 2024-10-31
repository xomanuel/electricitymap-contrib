import { HorizontalDivider } from 'components/Divider';
import BreakdownChart from 'features/charts/BreakdownChart';
import CarbonChart from 'features/charts/CarbonChart';
import EmissionChart from 'features/charts/EmissionChart';
import NetExchangeChart from 'features/charts/NetExchangeChart';
import PriceChart from 'features/charts/PriceChart';
import { TimeAverages } from 'utils/constants';

export default function AreaGraphContainer({
  datetimes,
  timeAverage,
  displayByEmissions,
}: {
  datetimes: Date[];
  timeAverage: TimeAverages;
  displayByEmissions: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      {displayByEmissions ? (
        <EmissionChart datetimes={datetimes} timeAverage={timeAverage} />
      ) : (
        <CarbonChart datetimes={datetimes} timeAverage={timeAverage} />
      )}
      <BreakdownChart
        displayByEmissions={displayByEmissions}
        datetimes={datetimes}
        timeAverage={timeAverage}
      />
      <NetExchangeChart datetimes={datetimes} timeAverage={timeAverage} />
      <PriceChart datetimes={datetimes} timeAverage={timeAverage} />
      <HorizontalDivider />
    </div>
  );
}
