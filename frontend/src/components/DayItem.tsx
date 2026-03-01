import React from 'react';
import type { DayNode } from '../utils/transformer';
import { CheckCircle2, Clock } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface DayItemProps {
  day: DayNode;
}

export const DayItem: React.FC<DayItemProps> = ({ day }) => {
  return (
    <div className="flex items-start gap-3 p-3 bg-white border border-gray-100 rounded-lg hover:shadow-sm transition-all">
      <div className="mt-1">
        {day.completed ? (
          <CheckCircle2 className="w-5 h-5 text-green-500" />
        ) : (
          <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />
        )}
      </div>
      <div className="flex-1">
        <h5 className="text-sm font-medium text-gray-800">{day.title}</h5>
        {day.description && (
          <p className="text-xs text-gray-500 mt-1">{day.description}</p>
        )}
        <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
          {day.task_date && (
            <span>
              {format(parseISO(day.task_date), 'MM月dd日 EEEE', { locale: zhCN })}
            </span>
          )}
          {day.estimated_hours && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {day.estimated_hours}h
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
