import React, { useState } from 'react';
import type { WeekNode } from '../utils/transformer';
import { DayItem } from './DayItem';
import { ChevronDown, ChevronRight, CalendarDays, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface WeekCardProps {
  week: WeekNode;
}

export const WeekCard: React.FC<WeekCardProps> = ({ week }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLeafTask = week.children.length === 0;

  return (
    <div className={`border rounded-lg overflow-hidden transition-all ${
        isLeafTask 
            ? 'bg-white border-blue-200 shadow-sm hover:shadow-md' 
            : 'bg-gray-50 border-gray-200'
    }`}>
      <div 
        className="p-3 cursor-pointer hover:bg-opacity-80 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex justify-between items-start gap-3">
            <div className="flex items-start gap-3 flex-1">
                <div className={`p-1.5 rounded-md shrink-0 ${
                    isLeafTask ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'
                }`}>
                    {isLeafTask ? <CheckCircle2 className="w-4 h-4" /> : <CalendarDays className="w-4 h-4" />}
                </div>
                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-semibold text-gray-800 truncate">{week.title}</h4>
                        {isLeafTask && (
                             <span className="px-1.5 py-0.5 text-[10px] font-medium text-green-700 bg-green-50 rounded border border-green-200 shrink-0">
                                独立任务
                            </span>
                        )}
                    </div>
                    
                    {/* Date Range */}
                    {(week.start_date || week.end_date) && (
                        <div className="text-[10px] text-gray-500 font-mono mb-1">
                            {week.start_date} ~ {week.end_date}
                        </div>
                    )}

                    <p className="text-xs text-gray-500 line-clamp-1">{week.description}</p>
                </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 self-center">
                {!isLeafTask && (
                    <span className="text-xs text-gray-400 bg-white px-2 py-0.5 rounded border border-gray-100">
                        {week.children.length} 任务
                    </span>
                )}
                
                {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
                ) : (
                <ChevronRight className="w-4 h-4 text-gray-400" />
                )}
            </div>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="p-3 space-y-2 border-t border-gray-200 bg-white">
              {week.children.length > 0 ? (
                week.children.map((day, index) => (
                  <DayItem key={index} day={day} />
                ))
              ) : (
                <div className="text-sm text-gray-600 py-2">
                    <p className="font-medium mb-1">任务详情：</p>
                    <p className="text-gray-500">{week.description || "暂无详细描述"}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
