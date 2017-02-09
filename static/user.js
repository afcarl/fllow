function datify(day_counts) {
    let total = 0;
    data = day_counts.map(day_count => {
        total += day_count[1];
        return {x: new Date(day_count[0] * 1000),
                y: total};
    });
    // add a dummy value with current time, for better chart range:
    data.push({x: new Date(), y: total});
    return data;
};

var chart = new Chartist.Line('.ct-chart', {
  series: [
    {
      name: 'follows',
      data: datify(FOLLOW_DAY_COUNTS)
    },
    {
      name: 'unfollows',
      data: datify(UNFOLLOW_DAY_COUNTS)
    },
    {
      name: 'followers',
      data: datify(FOLLOWER_DAY_COUNTS)
    }
  ]
}, {
  axisX: {
    type: Chartist.FixedScaleAxis,
    divisor: 5,
    labelInterpolationFnc: function(value) {
      return moment(value).format('MMM D');
    }
  }
});
