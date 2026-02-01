import { Newspaper, MapPin, Briefcase, Calendar, Trophy, Users, Laptop, TrendingUp, Heart, Cloud, UtensilsCrossed, Sparkles } from 'lucide-react';
import { Button } from './ui/button';

const iconMap = {
  Newspaper,
  MapPin,
  Briefcase,
  Calendar,
  Trophy,
  Users,
  Laptop,
  TrendingUp,
  Heart,
  Cloud,
  UtensilsCrossed,
  Sparkles
};

const CategoryNav = ({ categories, activeCategory, onCategoryChange }) => {
  return (
    <div className="bg-white shadow-sm border-b sticky top-0 z-10">
      <div className="container mx-auto px-2 sm:px-4 py-2">
        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          {categories.map((category) => {
            const Icon = iconMap[category.icon];
            const isActive = activeCategory === category.id;
            return (
              <Button
                key={category.id}
                variant={isActive ? 'default' : 'outline'}
                size="sm"
                onClick={() => onCategoryChange(category.id)}
                className={`transition-all text-[10px] sm:text-xs h-6 sm:h-8 px-2 sm:px-3 ${
                  isActive
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                    : 'hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300'
                }`}
              >
                <Icon className="h-2.5 w-2.5 sm:h-3 sm:w-3 mr-1 sm:mr-1.5" />
                {category.name}
              </Button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default CategoryNav;