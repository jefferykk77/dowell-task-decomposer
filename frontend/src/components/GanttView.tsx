import React, { useState, useEffect, useRef } from 'react';
import { Gantt, ViewMode, type Task } from 'gantt-task-react';
import "gantt-task-react/dist/index.css";
import type { DayNode, MonthNode, WeekNode, YearNode } from '../utils/transformer';
import { ConfirmModal } from './ConfirmModal';
import { assessImpact } from '../api/task';

// --- 类型转换 ---

interface GanttViewProps {
  data: YearNode;
  onTaskChange: (task: Task, changeType: 'move' | 'resize') => void;
}

const GanttView: React.FC<GanttViewProps> = ({ data, onTaskChange }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Day);
  const prevTasksRef = useRef<Task[]>([]); // 用于取消操作时的回滚
  
  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [pendingTask, setPendingTask] = useState<Task | null>(null);
  const [pendingChangeType, setPendingChangeType] = useState<'move' | 'resize'>('resize');
  const [aiSuggestion, setAiSuggestion] = useState<string>('');
  const [isLoadingAi, setIsLoadingAi] = useState(false);

  // 级联更新逻辑 (双向)
  const cascadeUpdate = (updatedTask: Task, currentTasks: Task[], changeType: 'move' | 'resize'): Task[] => {
    try {
        // 1. 找到原始任务
        const originalTask = currentTasks.find(t => t.id === updatedTask.id);
        if (!originalTask) return currentTasks;

        let newTasks = currentTasks.map(t => t.id === updatedTask.id ? updatedTask : t);

        // --- 向下更新 (Children) ---
        if (changeType === 'move' && originalTask.start.getTime() !== updatedTask.start.getTime()) {
            const delta = updatedTask.start.getTime() - originalTask.start.getTime();
            
            const recursiveUpdateChildren = (parentId: string, list: Task[]): Task[] => {
                const children = list.filter(t => t.project === parentId);
                if (children.length === 0) return list;

                let updatedList = [...list];
                children.forEach(child => {
                    const newStart = new Date(child.start.getTime() + delta);
                    const newEnd = new Date(child.end.getTime() + delta);
                    const newChild = { ...child, start: newStart, end: newEnd };
                    
                    updatedList = updatedList.map(t => t.id === child.id ? newChild : t);
                    updatedList = recursiveUpdateChildren(child.id, updatedList);
                });
                return updatedList;
            };

            newTasks = recursiveUpdateChildren(updatedTask.id, newTasks);
        }

        // --- 向上更新 (Parents) ---
        const updateParent = (taskId: string, tasksList: Task[]): Task[] => {
          const task = tasksList.find(t => t.id === taskId);
          if (!task || !task.project) return tasksList; 

          const parentId = task.project;
          const parent = tasksList.find(t => t.id === parentId);
          if (!parent) return tasksList;

          const children = tasksList.filter(t => t.project === parentId);
          const childStarts = children.map(c => c.start.getTime());
          const childEnds = children.map(c => c.end.getTime());
          
          if (childStarts.length === 0) return tasksList;

          const newStart = Math.min(...childStarts);
          const newEnd = Math.max(...childEnds);

          let minStart = parent.start.getTime();
          let maxEnd = parent.end.getTime();
          let changed = false;

          // 父任务必须包容所有子任务
          if (newStart < minStart) {
              minStart = newStart;
              changed = true;
          }
          if (newEnd > maxEnd) {
               maxEnd = newEnd;
               changed = true;
          }

          if (changed) {
              const updatedParent = {
                  ...parent,
                  start: new Date(minStart),
                  end: new Date(maxEnd)
              };
              
              const updatedList = tasksList.map(t => t.id === parentId ? updatedParent : t);
              return updateParent(parentId, updatedList);
          }

          return tasksList;
        };

        return updateParent(updatedTask.id, newTasks);
    } catch (e) {
        console.error("Cascade update error:", e);
        return currentTasks; // 出错时返回原状态
    }
  };

  const handleTaskChange = async (task: Task) => {
    const originalTask = tasks.find(t => t.id === task.id);
    if (!originalTask) return;

    // 1. 保存当前状态用于回滚
    prevTasksRef.current = tasks;

    // 2. 判断变更类型
    let changeType: 'move' | 'resize' = 'resize';
    const originalSpan = originalTask.end.getTime() - originalTask.start.getTime();
    const newSpan = task.end.getTime() - task.start.getTime();
    if (Math.abs(originalSpan - newSpan) < 1000) {
        changeType = 'move';
    }

    // 3. 乐观更新 (立即计算并应用新状态，防止 UI 闪烁)
    const newTasks = cascadeUpdate(task, tasks, changeType);
    setTasks(newTasks);

    // 4. 设置 Modal 状态
    setPendingTask(task);
    setPendingChangeType(changeType);
    setModalOpen(true);
    setIsLoadingAi(true);
    setAiSuggestion('');

    // 5. 调用 AI 评估
    try {
        const childrenCount = tasks.filter(t => t.project === task.id).length;
        const reqData = {
            original_task: {
                title: originalTask.name,
                start_date: originalTask.start.toISOString().split('T')[0],
                end_date: originalTask.end.toISOString().split('T')[0],
            },
            updated_task: {
                title: task.name,
                start_date: task.start.toISOString().split('T')[0],
                end_date: task.end.toISOString().split('T')[0],
            },
            parent_task: {
                title: "上级任务", 
                start_date: "2024-01-01",
                end_date: "2024-12-31",
                description: "Parent task context"
            },
            change_type: changeType,
            context: {
                is_parent: childrenCount > 0,
                children_affected_count: childrenCount
            }
        };
        const assessment = await assessImpact(reqData);
        
        let suggestion = assessment.suggestion || "无明显风险";
        if (childrenCount > 0) {
            suggestion += ` (注意：此操作将同时移动 ${childrenCount} 个直接下级任务)`;
        }
        setAiSuggestion(suggestion);
    } catch (e) {
        console.error("AI assess failed", e);
        setAiSuggestion("AI 评估服务暂时不可用，请自行确认。");
    } finally {
        setIsLoadingAi(false);
    }
  };

  const confirmChange = () => {
    if (pendingTask) {
        // UI 已经在 handleTaskChange 中更新了，这里只需要通知父组件
        onTaskChange(pendingTask, pendingChangeType);
    }
    setModalOpen(false);
    setPendingTask(null);
    setAiSuggestion('');
  };

  const cancelChange = () => {
    // 回滚到之前的状态
    if (prevTasksRef.current.length > 0) {
        setTasks(prevTasksRef.current);
    }
    setModalOpen(false);
    setPendingTask(null);
    setAiSuggestion('');
  };

  // 将树状数据展平为 Gantt Task 列表
  useEffect(() => {
    const flatTasks: Task[] = [];
    
    // 1. Year
    const yearTask: Task = {
      start: new Date(data.start_date || new Date()),
      end: new Date(data.end_date || new Date()),
      name: data.title,
      id: 'year',
      type: 'task', // 改为 task 以支持拖拽
      progress: 0,
      isDisabled: false, // 允许拖拽
      hideChildren: false,
      styles: { progressColor: '#4f46e5', progressSelectedColor: '#3730a3' } // Indigo
    };
    flatTasks.push(yearTask);

    // 2. Months
    if (data.children && data.children.length > 0) {
      data.children.forEach((child, mIdx: number) => {
        if (child.type !== 'month') return;
        const month: MonthNode = child;
        const monthId = `month-${mIdx}`;
        flatTasks.push({
          start: new Date(month.start_date || new Date()),
          end: new Date(month.end_date || new Date()),
          name: month.title,
          id: monthId,
          type: 'task', // 改为 task 以支持拖拽
          progress: 0,
          project: 'year',
          hideChildren: false,
          styles: { progressColor: '#0ea5e9', progressSelectedColor: '#0284c7' } // Sky Blue
        });

        // 3. Weeks
        if (month.children && month.children.length > 0) {
            month.children.forEach((weekChild, wIdx: number) => {
                if (weekChild.type !== 'week') return;
                const week: WeekNode = weekChild;
                const weekId = `week-${mIdx}-${wIdx}`;
                flatTasks.push({
                    start: new Date(week.start_date || new Date()),
                    end: new Date(week.end_date || new Date()),
                    name: week.title,
                    id: weekId,
                    type: 'task', // 改为 task 以支持拖拽
                    progress: 0,
                    project: monthId,
                    hideChildren: false,
                    styles: { progressColor: '#8b5cf6', progressSelectedColor: '#7c3aed' } // Violet
                });

                // 4. Days
                if (week.children && week.children.length > 0) {
                    week.children.forEach((dayChild, dIdx: number) => {
                        if (dayChild.type !== 'day') return;
                        const day: DayNode = dayChild;
                        const dayId = `day-${mIdx}-${wIdx}-${dIdx}`;
                        flatTasks.push({
                            start: new Date(day.task_date || new Date()), // task_date 是一天
                            end: new Date(new Date(day.task_date || new Date()).getTime() + (day.estimated_hours || 2) * 3600 * 1000), // 估时转换为毫秒
                            name: day.title,
                            id: dayId,
                            type: 'task',
                            progress: day.completed ? 100 : 0,
                            project: weekId,
                            // 保存原始数据引用以便查找 parent
                            // dependencies: ...
                        });
                    });
                }
            });
        }
      });
    } else {
        // 如果没有月/周层级，尝试直接挂载 Days (根据之前的逻辑修复，可能存在这种情况)
        // 但目前 transformer.ts 还是 full hierarchy。
        // 为了兼容性，这里暂时只处理标准层级。
        // 如果要处理 Year -> Days，需要修改 transformer.ts 或在这里做深度遍历。
    }

    setTasks(flatTasks);
  }, [data]);

  // 旧的 handleTaskChange, 被新的替代，这里删除或注释掉
  // ...

  const handleProgressChange = async (task: Task) => {
    setTasks(tasks.map(t => (t.id === task.id ? task : t)));
    console.log("On progress change", task.id);
  };

  const handleDblClick = (task: Task) => {
    alert("On Double Click event Id:" + task.id);
  };

  const handleSelect = (task: Task, isSelected: boolean) => {
    console.log(task.name + " has " + (isSelected ? "selected" : "unselected"));
  };

  const handleExpanderClick = (task: Task) => {
    setTasks(tasks.map(t => (t.id === task.id ? task : t)));
    console.log("On expander click Id:" + task.id);
  };

  const getColumnWidth = (mode: ViewMode) => {
    switch (mode) {
      case ViewMode.Year:
        return 350;
      case ViewMode.Month:
        return 300;
      case ViewMode.Week:
        return 250;
      case ViewMode.Day:
      default:
        return 65;
    }
  };

  const getFilteredTasks = () => {
    switch (viewMode) {
        case ViewMode.Day:
            // 只显示日任务 (id 以 day- 开头)
            return tasks.filter(t => t.id.startsWith('day-')).map(t => ({...t, project: undefined}));
        case ViewMode.Week:
            // 只显示周任务 (id 以 week- 开头)
            return tasks.filter(t => t.id.startsWith('week-')).map(t => ({...t, project: undefined}));
        case ViewMode.Month:
            // 只显示月任务 (id 以 month- 开头)
            return tasks.filter(t => t.id.startsWith('month-')).map(t => ({...t, project: undefined}));
        case ViewMode.Year:
            // 年视图显示年任务 (或者全部？根据用户语境，可能倾向于只看年)
            // 这里我们显示年任务 + 月任务作为概览，或者只显示年任务
            // 既然用户强调"只显示X"，那年视图暂且只显示年任务，或者保持全貌。
            // 考虑到年视图通常作为总览，显示年任务比较合理。
            return tasks.filter(t => t.id === 'year');
        default:
            return tasks;
    }
  };

  const visibleTasks = getFilteredTasks();

  return (
    <div className="p-4 bg-white rounded-xl shadow-lg overflow-x-auto relative">
        <ConfirmModal 
            isOpen={modalOpen}
            title="确认调整时间"
            message={`您将任务 "${pendingTask?.name}" 的时间调整为 ${pendingTask?.start.toLocaleDateString()} - ${pendingTask?.end.toLocaleDateString()}。此操作将同步更新所有上级任务。`}
            suggestion={aiSuggestion}
            isLoading={isLoadingAi}
            onConfirm={confirmChange}
            onCancel={cancelChange}
        />

        <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
            <button onClick={() => setViewMode(ViewMode.Day)} className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${viewMode === ViewMode.Day ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>日视图</button>
            <button onClick={() => setViewMode(ViewMode.Week)} className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${viewMode === ViewMode.Week ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>周视图</button>
            <button onClick={() => setViewMode(ViewMode.Month)} className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${viewMode === ViewMode.Month ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>月视图</button>
            <button onClick={() => setViewMode(ViewMode.Year)} className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${viewMode === ViewMode.Year ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>年视图</button>
        </div>
        
        {visibleTasks.length > 0 ? (
             <Gantt
             tasks={visibleTasks}
             viewMode={viewMode}
             onDateChange={handleTaskChange}
             onDelete={() => {}}
             onProgressChange={handleProgressChange}
             onDoubleClick={handleDblClick}
             onSelect={handleSelect}
             onExpanderClick={handleExpanderClick}
             listCellWidth="160px"
             columnWidth={getColumnWidth(viewMode)}
             locale="zh"
             barFill={60}
             barCornerRadius={6}
             fontFamily="inherit"
           />
        ) : (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                <p>暂无任务数据</p>
            </div>
        )}
     
    </div>
  );
};

export default GanttView;
