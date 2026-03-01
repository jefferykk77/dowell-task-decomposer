import React from 'react';
import type { YearNode, MonthNode, WeekNode, DayNode } from '../utils/transformer';
import { MonthCard } from './MonthCard';
import { WeekCard } from './WeekCard';
import { DayItem } from './DayItem';
import { Flag, Calendar } from 'lucide-react';

interface YearViewProps {
  data: YearNode;
}

export const YearView: React.FC<YearViewProps> = ({ data }) => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Annual Header Card */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-12 opacity-10 transform translate-x-1/3 -translate-y-1/3">
          <Flag className="w-64 h-64" />
        </div>
        
        <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2 opacity-80">
                <Calendar className="w-5 h-5" />
                <span className="text-sm font-medium tracking-wider uppercase">Annual Goal</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">{data.title}</h1>
            <p className="text-blue-100 text-lg max-w-2xl">{data.description}</p>
            
            {data.milestones && data.milestones.length > 0 && (
            <div className="mt-8 pt-6 border-t border-white/20">
                <h4 className="text-sm font-semibold mb-3 opacity-90">关键里程碑</h4>
                <div className="flex flex-wrap gap-3">
                {data.milestones.map((m, i) => (
                    <span key={i} className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm">
                    🏁 {m}
                    </span>
                ))}
                </div>
            </div>
            )}
        </div>
      </div>

      {/* Children Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {data.children.map((item, index) => {
            if (item.type === 'month') {
                return <MonthCard key={index} month={item as MonthNode} />;
            } else if (item.type === 'week') {
                return <WeekCard key={index} week={item as WeekNode} />;
            } else if (item.type === 'day') {
                return <DayItem key={index} day={item as DayNode} />;
            }
            return null;
        })}
      </div>
    </div>
  );
};
