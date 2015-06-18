require(['jquery','underscore','splunkjs/mvc','util/console','splunkjs/mvc/simplexml/ready!'], function($, _, mvc, console, Dashboard){

         // Get a reference to the dashboard panels
        var masterView = mvc.Components.get('master');
        var detailView = mvc.Components.get('detail');
        //var flameView = mvc.Components.get('flame');

        var unsubmittedTokens = mvc.Components.get('default');
        var submittedTokens = mvc.Components.get('submitted');
        var urlTokens = mvc.Components.get('url');

        if(!submittedTokens.has('threadid')) {
            // if there's no value for the $sourcetype$ token yet, hide the dashboard panel of the detail view
            detailView.$el.parents('.dashboard-panel').hide();
            //flameView.$el.parents('.dashboard-panel').hide();
        }

        // submittedTokens.on('change:threadid', function(){
        //     // When the token changes...
        //     if(!submittedTokens.get('threadid')) {
        //         // ... hide the panel if the token is not defined
        //         detailView.$el.parents('.dashboard-panel').hide();
        //         //flameView.$el.parents('.dashboard-panel').hide();
        //     } else {
        //         // ... show the panel if the token has a value
        //         detailView.$el.parents('.dashboard-panel').show();
        //         //flameView.$el.parents('.dashboard-panel').show();
        //     }
        // });
        masterView.on('click', function(e) {
            e.preventDefault();
            var newValue = "",
                clickValue = e.data['click.name2'],
                currentValue = unsubmittedTokens.get('form.threadid') || submittedTokens.get('form.threadid') || "";

            currentValue = currentValue.split(',');
            
            if (_.contains(currentValue, clickValue)) {
                newValue = _.difference(currentValue,[clickValue]);
            }else{
                newValue = _.union(currentValue, [clickValue]);
            }

            // get rid of empty value
            newValue = _.difference(newValue, [""]);

            // Submit the value for the sourcetype field
            if (newValue.length===0) {
                unsubmittedTokens.set('form.threadid', undefined);
            }else{
                unsubmittedTokens.set('form.threadid', newValue.toString());
            }
            submittedTokens.set(unsubmittedTokens.toJSON());
            urlTokens.saveOnlyWithPrefix('form\\.', unsubmittedTokens.toJSON(), {
                replaceState: false
            });

            //
        });
});
