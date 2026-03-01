import React, { useState } from 'react';
import type { MonthNode } from '../utils/transformer';
import { WeekCard } from './WeekCard';
import { cn } from '../utils/cn';
import { CalendarRange, Box } from 'lucide-react';

interface MonthCardProps {
  month: MonthNode;
}

export const MonthCard: React.FC<MonthCardProps> = ({ month }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLeafTask = month.children.length === 0;

  return (
    <div className={cn(
      "border rounded-xl transition-all duration-300 relative overflow-hidden",
      isExpanded 
        ? "bg-white border-blue-200 shadow-md col-span-1 md:col-span-2 lg:col-span-3" 
        : isLeafTask
          ? "bg-gradient-to-br from-blue-50 to-white border-blue-200 shadow-sm"
          : "bg-white border-gray-200 hover:border-blue-300 hover:shadow-sm"
    )}>
      {isLeafTask && (
        <div className="absolute top-0 right-0 p-2 opacity-10">
           <Box className="w-24 h-24 text-blue-600 transform rotate-12" />
        </div>
      )}
      
      <div className="p-4 relative z-10">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg font-bold text-gray-800">{month.title}</h3>
                {isLeafTask && (
                    <span className="px-2 py-0.5 text-xs font-medium text-blue-700 bg-blue-100 rounded-full border border-blue-200">
                        月度专项
                    </span>
                )}
            </div>
            
            {/* Date Range Display */}
            {(month.start_date || month.end_date) && (
                <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2 font-mono">
                    <CalendarRange className="w-3.5 h-3.5" />
                    <span>{month.start_date} ~ {month.end_date}</span>
                </div>
            )}

            <p className="text-sm text-gray-500 mt-1 line-clamp-2">{month.description}</p>
          </div>
          
          {!isLeafTask && (
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="ml-4 text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-600 font-medium transition-colors shrink-0"
            >
                {isExpanded ? '收起详情' : '查看周计划'}
            </button>
          )}
        </div>

        {isExpanded && !isLeafTask && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4 border-t border-gray-100 pt-4 animate-in fade-in slide-in-from-top-2">
            {month.children.map((week, index) => (
              <WeekCard key={index} week={week} />
            ))}
          </div>
        )}
        
        {!isExpanded && !isLeafTask && (
           <div className="flex gap-2 mt-2 overflow-hidden">
                {month.children.slice(0, 4).map((_, i) => (
                    <div key={i} className="h-1.5 w-full bg-blue-100 rounded-full" />
                ))}
           </div>
        )}
      </div>
    </div>
  );
};
