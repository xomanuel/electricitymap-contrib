import { MoreOptionsDropdown, useShowMoreOptions } from 'components/MoreOptionsDropdown';
import { Ellipsis } from 'lucide-react';
import { Charts } from 'utils/constants';

type Props = {
  titleText?: string;
  unit?: string;
  badge?: React.ReactElement;
  className?: string;
  isEstimated?: boolean;
  id?: Charts;
};

export function ChartTitle({
  titleText,
  unit,
  badge,
  className,
  isEstimated,
  id,
}: Props) {
  const showMoreOptions = useShowMoreOptions();
  return (
    <div className="flex flex-col pb-0.5">
      <div className={`flex items-center gap-1.5 pt-4 ${className}`}>
        <h2 id={id} className="grow">
          {titleText}
        </h2>
        {badge}
        {showMoreOptions && (
          <MoreOptionsDropdown isEstimated={isEstimated}>
            <Ellipsis />
          </MoreOptionsDropdown>
        )}
      </div>
      {unit && <div className="text-sm dark:text-gray-300">{unit}</div>}
    </div>
  );
}
