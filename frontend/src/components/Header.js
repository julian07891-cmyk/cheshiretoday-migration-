const Header = () => {
  return (
    <header className="bg-gradient-to-r from-emerald-700 to-emerald-900 text-white shadow-lg">
      <div className="container mx-auto px-2 sm:px-4 py-2 sm:py-4 md:py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 sm:space-x-4">
            <img 
              src="/logo.png" 
              alt="Cheshire Today Logo" 
              className="h-8 sm:h-12 md:h-14 w-auto object-contain bg-white rounded-lg px-1 sm:px-2 py-0.5 sm:py-1"
            />
            <div>
              <h1 className="text-base sm:text-2xl md:text-3xl font-bold tracking-tight">Cheshire Today</h1>
              <p className="text-emerald-100 text-[10px] sm:text-xs md:text-sm mt-0.5 sm:mt-1">Local News & Updates</p>
            </div>
          </div>
          <div className="text-right hidden sm:block">
            <p className="text-xs sm:text-sm text-emerald-100">{new Date().toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;