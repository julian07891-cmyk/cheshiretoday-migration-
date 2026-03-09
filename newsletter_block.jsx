              <div className="mt-8 p-5 rounded-xl border border-slate-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/50">
                <h3 className="text-lg font-extrabold tracking-tight mb-2">
                  Get the Cheshire Today Daily Brief
                </h3>

                <p className="text-sm text-slate-600 dark:text-gray-400 mb-4">
                  Local news, business, finance and AI updates delivered every morning.
                </p>

                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    const email = e.target.email.value;

                    try {
                      const res = await fetch(`${getApiUrl()}/api/subscribe`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email })
                      });

                      if (res.ok) {
                        toast({
                          title: "Subscribed",
                          description: "You will receive the Daily Brief."
                        });
                        e.target.reset();
                      } else {
                        toast({
                          title: "Subscription failed",
                          description: "Please try again later."
                        });
                      }
                    } catch {
                      toast({
                        title: "Subscription error",
                        description: "Please try again later."
                      });
                    }
                  }}
                >
                  <div className="flex gap-2">
                    <input
                      name="email"
                      type="email"
                      required
                      placeholder="Your email address"
                      className="flex-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                    />

                    <button
                      type="submit"
                      className="px-4 py-2 text-sm font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700"
                    >
                      Subscribe
                    </button>
                  </div>
                </form>
              </div>
