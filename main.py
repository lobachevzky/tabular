import time
import itertools

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation

import algorithm
from algorithm import stochastic_stepwise_transitions


def circle_color(i, terminal):
    if terminal:
        return 'white'
    elif i == 0:
        return 'black'
    else:
        return 'gray'


def updatefig(ax, agent, speed):
    ax.axis('off')
    ax.set_ylim([-1, agent.n_agents])
    im = ax.imshow(agent.rewards, vmin=0, vmax=1,
                   cmap='Oranges', animated=True)
    im.set_zorder(0)
    timestep_text = ax.text(.5, 0, '',
                            verticalalignment='bottom',
                            horizontalalignment='center',
                            transform=ax.transAxes, zorder=2)

    circles = []
    texts = []
    for i in range(agent.n_agents):
        for j in range(agent.n_states):
            texts.append(ax.text(j, i, int(round(agent.rewards[i, j])),
                                 zorder=2))
        circle = plt.Circle([0, 0], radius=0.2,
                            zorder=1, edgecolor='white')
        circles.append(circle)
        ax.add_patch(circle)

    total_reward = 0
    total_advantage = 0
    value_matrix = np.zeros_like(agent.rewards)
    for episode in itertools.count(1):
        states = agent.reset()
        done = np.zeros_like(states, dtype=bool)
        pos = states.astype(float)
        for timestep in range(agent.max_timesteps):

            step_result = agent.step(states, value_matrix, done)
            actions, next_states, reward, vm_pre_optimization, done = step_result
            value_matrix = agent.apply_triangle_inequality(vm_pre_optimization)
            advantage = np.sum(value_matrix[0] - vm_pre_optimization[0])
            total_advantage += advantage
            assert np.array_equal(states[done], next_states[done])

            if not done[0]:
                total_reward += reward[0]
            step_size = (next_states - states) * speed
            assert np.all(step_size[done] == 0)

            value = np.sum(value_matrix[0])
            advantage_percent = total_advantage / value * 100
            timestep_text.set_text(
                'reward: {} optimization: {:.2f}%'.format(
                    total_reward, advantage_percent))
            im.set_array(value_matrix)
            for i, (state, terminal, circle) in enumerate(zip(states, agent.terminal, circles)):
                circle.set_facecolor(circle_color(i, state == terminal))
            while not np.allclose(pos, next_states):
                pos += step_size
                for i, j in enumerate(pos):
                    circles[i].center = (j, i)
                yield [im, timestep_text] + texts + circles

            states = next_states

            if not done[0]:
                total_reward += reward[0]

        # time.sleep(.5)




def identity(x):
    return x


if __name__ == '__main__':
    np.set_printoptions(precision=1)
    n_states = 20
    transitions = algorithm.combination_lock_transitions(sigma=.5, n_states=n_states)
    # transitions = algorithm.stochastic_stepwise_transitions(sigma=.5, n_states=n_states)
    rewards = np.zeros(n_states)
    # rewards[0] = 1
    rewards[[0, -1]] = [.001, .999]
    # rewards[np.random.choice(n_states)] = 1
    agent1 = algorithm.OptimizedSingleAgent(
        gamma=.95,
        alpha=.9,
        n_states=n_states,
        n_actions=2,
        transitions=transitions,
        max_timesteps=15,
        # n_agents=n_agents,
        rewards=rewards,
    )

    agent2 = algorithm.Agent(
        gamma=.95,
        alpha=.9,
        n_states=n_states,
        n_agents=1,
        n_actions=2,
        transitions=transitions,
        max_timesteps=n_states,
        rewards=agent1.rewards[[0]],
        terminal=agent1.rewards[[0]].argmax(axis=1),
    )
    # agent2 = algorithm.OptimizedAgent( gamma=.95,
    #     alpha=.95,
    #     n_states=n_states,
    #     n_actions=2,
    #     transitions=transitions,
    #     max_timesteps=15,
    #     # n_agents=n_agents,
    #     rewards=agent1.rewards[0],
    # )

    # fig, (ax1, ax2) = plt.subplots(2)
    fig, ax1 = plt.subplots(1)
    ax1.set_title('Optimized Agent')
    # ax2.set_title('Baseline Agent')
    speed = 1 / 2


    def animate():
        artists1 = updatefig(ax1, agent1, speed)
        # artists2 = updatefig(ax2, agent2, speed)
        while True:
            yield next(artists1) #+ next(artists2)


    a1 = animation.FuncAnimation(fig, identity, animate,
                                 interval=1, blit=True)

    plt.show()
